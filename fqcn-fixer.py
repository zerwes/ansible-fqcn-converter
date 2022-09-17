#! /usr/bin/env python3
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent
# pylint: disable=invalid-name

import sys
import os
import subprocess
import argparse
import json
import re
import fileinput
import difflib
import fnmatch
import pathlib
import copy
import yaml

__doc__ = """
simple script to fix the fqcn module names
"""

def isexcluded(path, _exclude_paths):
    """check if a path element should be excluded"""
    ppath = pathlib.PurePath(path)
    path = os.path.abspath(path)
    return any(
        path.startswith(ep)
        or
        path.startswith(os.path.abspath(ep))
        or
        ppath.match(ep)
        or
        fnmatch.fnmatch(path, ep)
        or
        fnmatch.fnmatch(ppath, ep)
        for ep in _exclude_paths
        )

def debugmsg(msg):
    """debug msg"""
    print(msg, file=sys.stderr, flush=True)

def checkignoreregex(line):
    """check if we should ignore replacement"""
    for exre in _general_exclude_regex:
        if exre.match(line):
            return True
    return False

class Dumper(yaml.Dumper): # pylint: disable=too-many-ancestors
    """https://github.com/yaml/pyyaml/issues/234"""
    def increase_indent(self, flow=False, *dargs): # pylint: disable=keyword-arg-before-vararg
        return super().increase_indent(dargs, indentless=False)

basepath = os.path.dirname(os.path.realpath(__file__))

# this will be excluded
_general_exclude_paths = [
    ".cache",
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".collections",
    "*/.github/*",
    "*/molecule/*",
    "*/group_vars/*",
    "*/host_vars/*",
    "*/vars/*",
    "*/defaults/*",
    "*/meta/*",
    ]

# case insensitive list of regex to exclude / skip replacements
_general_exclude_regex = [
    re.compile('\s*gather_facts:\s*(no|yes|true|false)', re.IGNORECASE),
]

required_fqcnconverter_file_version = '0.0.5'

argparser = argparse.ArgumentParser(description=__doc__)
argparser.add_argument(
    '-d', '--directory',
    type=str,
    dest='directory',
    default='.',
    help="directory to search files (default: current directory)"
    )
argparser.add_argument(
    '-e', '--extensions',
    type=str, nargs='+',
    dest='fileextensions',
    default=['yml', 'yaml'],
    help='list of file extensions to use (default: \'yml\', \'yaml\')'
    )
argparser.add_argument(
    '--exclude',
    dest="exclude_paths",
    type=str, nargs='+',
    default=[],
    help="path(s) to directories or files to skip.",
    )
argparser.add_argument(
    '--do-not-use-default-exclude',
    dest="no_general_exclude_paths",
    action='store_true',
    default=False,
    help="do not use the default excludes",
    )
argparser.add_argument(
    '-c', '--config',
    dest="config",
    type=str,
    help="read some cfg args from this file (.ansible-lint can be used)",
    )
argparser.add_argument(
    '-w', '--write-files',
    dest='writefiles',
    action='store_true',
    default=False,
    help="write back changed files"
    )
argparser.add_argument(
    '-W', '--no-write-warnings',
    dest='writewarnings',
    action='store_false',
    default=True,
    help="do not write warnings as comments to files and diff"
    )
argparser.add_argument(
    '-b', '--backup-extension',
    dest='backupextension',
    default='.bak',
    help="backup extension to use (default: .bak)"
    )
argparser.add_argument(
    '-x', '--no-diff',
    dest='printdiff',
    action='store_false',
    default=True,
    help="do not print a diff after parsing a file (default: print it)"
    )
argparser.add_argument(
    '-m', '--fqcn-map-file',
    type=str,
    dest='fqcnmapfile',
    default='%s' % os.path.join(basepath, 'fqcn.yml'),
    help="yaml file to use for the fqcn map (default: %s)" % os.path.join(basepath, 'fqcn.yml')
    )
argparser.add_argument(
    '-u', '--update-fqcn-map-file',
    dest='updatefqcnmapfile',
    action='store_true',
    default=False,
    help="update the fqcn-map-file"
    )
argparser.add_argument(
    '-D', '--debug',
    dest='debug',
    action='store_true',
    default=False,
    help="update the fqcn-map-file"
    )

args = argparser.parse_args()

# get a dict of ansible modules
fqcndict = {}
fqcnmapfile = True
if not args.updatefqcnmapfile:
    try:
        with open(args.fqcnmapfile, "r") as fqcnf:
            fqcndict = yaml.load(fqcnf, Loader=yaml.BaseLoader)
            if fqcndict['__fqcnconverter_file_version__'] != required_fqcnconverter_file_version:
                print('fqcnconverter_file_version missmatch: got %s but expected %s' %
                    (fqcndict['__fqcnconverter_file_version__'],
                        required_fqcnconverter_file_version,)
                    )
                fqcnmapfile = False
    except (FileNotFoundError, KeyError) as fqcnmapfilerror:
        print(fqcnmapfilerror)
        fqcnmapfile = False

if not fqcnmapfile or args.updatefqcnmapfile:
    print('we will generate the fqcn map, this will take some time ...')
    fqcndict = {'__fqcnconverter_file_version__': required_fqcnconverter_file_version}
    modulespr = subprocess.run(
        ['ansible-doc', '-lj'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check = True
        )
    modulesdict = json.loads(modulespr.stdout)
    for modname in modulesdict.keys():
        modpr = subprocess.run(
            ['ansible-doc', '-j', modname],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check = False
            )
        if modpr.returncode > 0:
            print('error parsing %s' % modname)
            continue
        modjson = json.loads(modpr.stdout)
        if not modjson or not modname in modjson.keys():
            print('error: no informations for %s' % modname)
            continue
        moddict = modjson[modname]
        if 'doc' in moddict and 'collection' in moddict['doc'] and 'module' in moddict['doc']:
            fqcn = '%s.%s' % (moddict['doc']['collection'], moddict['doc']['module'])
            nonfqcn = fqcn.split('.')[-1]
            if nonfqcn not in fqcndict.keys():
                fqcndict[nonfqcn] = []
            if fqcn not in fqcndict[nonfqcn]:
                fqcndict[nonfqcn].append(fqcn)
            print('%s : %s -> %s' % (modname, nonfqcn, fqcn))
    fqcnmapfile = open(args.fqcnmapfile, 'w')
    fqcnmapfile.write(
        yaml.dump(
            fqcndict,
            Dumper=Dumper,
            sort_keys=True,
            indent=2,
            width=70,
            explicit_start=True,
            explicit_end=True,
            default_flow_style=False
            )
        )
    fqcnmapfile.close()
    print('fqcn map written to %s' % args.fqcnmapfile)

# add the fqcn as key to
for fqcnlist in copy.copy(fqcndict).values():
    for fqcn in fqcnlist:
        fqcndict[fqcn] = [fqcn]

# build exclude_paths
exclude_paths = []
for ep in args.exclude_paths:
    exclude_paths.append(ep)
if not args.no_general_exclude_paths:
    for ep in _general_exclude_paths:
        exclude_paths.append(ep)
exclude_paths.append(args.fqcnmapfile)

# update some args from optional config file
_config = {}
if args.config:
    try:
        with open(args.config) as ymlfile:
            _config = yaml.load(ymlfile, Loader=yaml.BaseLoader)
    except FileNotFoundError:
        pass
if _config and 'exclude_paths' in _config.keys():
    for ep in _config['exclude_paths']:
        exclude_paths.append(os.path.abspath(ep))

# find files to parse
parsefiles = []
for dirpath, dirnames, files in os.walk(os.path.abspath(args.directory)):
    if isexcluded(dirpath, exclude_paths):
        continue
    for name in files:
        for ext in args.fileextensions:
            if name.lower().endswith(ext.lower()):
                f = os.path.join(dirpath, name)
                if isexcluded(f, exclude_paths):
                    break
                parsefiles.append(f)

# prepare regex
_fqcnregex = re.compile(r'^(?P<white>\s*-?\s+)(?P<module>%s):' % '|'.join(fqcndict.keys()))
_taskstartregex = re.compile(
    r'^(?P<white>\s*-\s+)(?P<nm>%s):' %
        '|'.join(['name'] + list(fqcndict.keys()))
    )

# do it
for f in parsefiles:
    print('parsing file %s ' % f, file=sys.stderr, end='', flush=True)
    warnings = []
    with fileinput.input(f,
            inplace=args.writefiles,
            backup=args.backupextension) as fi:
        originallines = []
        changedlines = []
        startingwhitespaces = '\s*-?\s+'
        startingwhitespacesaftertask = 0
        startingwhitespaces4comments = 0
        in_task = False
        in_task_done = False
        fqcnregex = _fqcnregex
        for line in fi:
            if args.debug:
                debugmsg(
                    'STARTLINE : line: %s in_task: %s in_task_done: %s\n' %
                    (line, in_task, in_task_done,)
                    )
            if args.printdiff:
                originallines.append(line)
            nline = line
            taskmatch = _taskstartregex.match(line)
            if taskmatch:
                in_task_done = False
                in_task = False
            if in_task_done and not taskmatch:
                if args.debug:
                    debugmsg('SKIPLINE! %s\n' % (in_task_done and not in_task))
                print('.', file=sys.stderr, end='', flush=True)
            else:
                if not in_task:
                    if args.debug:
                        debugmsg('TASKMATCH : line: %s taskmatch: %s\n' % (line, taskmatch,))
                    if taskmatch:
                        in_task = True
                        in_task_done = False
                        startingwhitespacesaftertask = len(taskmatch.group('white'))
                        if args.debug:
                            debugmsg(
                                'line: %s startingwhitespacesaftertask: %s taskmatch: %s' %
                                (line, startingwhitespacesaftertask, taskmatch,)
                                )
                fqcnmatch = fqcnregex.match(line)
                if args.debug:
                    debugmsg('FQCNMATCH : line: %s fqcnmatch: %s\n' % (line, fqcnmatch,))
                    #debugmsg('fqcnregex: %s' % fqcnregex)
                if fqcnmatch and not checkignoreregex(line):
                    in_task_done = True
                    in_task = False
                    fqcnmodule = fqcnmatch.group('module')
                    nline = re.sub(
                        '^(%s)%s:' % (startingwhitespaces, fqcnmodule),
                        '\\1%s:' % fqcndict[fqcnmodule][0],
                        line
                        )
                    if fqcnmodule == fqcndict[fqcnmodule][0]:
                        print('.', file=sys.stderr, end='', flush=True)
                    else:
                        print('*', file=sys.stderr, end='', flush=True)
                        if len(fqcndict[fqcnmodule]) > 1:
                            wtxt = ('possible ambiguous replacement: %s : %s' %
                                   (fqcnmodule, ' | '.join(fqcndict[fqcnmodule])))
                            warnings.append(wtxt)
                            if args.writewarnings:
                                if args.writefiles:
                                    print('%s# %s' % (' '*startingwhitespaces4comments, wtxt))
                                if args.printdiff:
                                    changedlines.append(
                                        '%s# %s\n' % (' '*startingwhitespaces4comments, wtxt)
                                        )
                else:
                    print('.', file=sys.stderr, end='', flush=True)
                    if startingwhitespacesaftertask > 0:
                        startingwhitespaces = ' ' * startingwhitespacesaftertask
                        startingwhitespaces4comments = startingwhitespacesaftertask
                        startingwhitespacesaftertask = 0
                        fqcnregex = re.compile('^%s(?P<module>%s):' %
                            (startingwhitespaces, '|'.join(fqcndict.keys()))
                            )
                        if args.debug:
                            debugmsg('set STARTINGWHITESPACES to "%s"' % startingwhitespaces)

            if args.writefiles:
                print(nline, end='')
            if args.printdiff:
                changedlines.append(nline)
        print('', file=sys.stderr)
        if args.printdiff:
            diff = difflib.unified_diff(
                originallines,
                changedlines,
                fromfile='a/%s' % f,
                tofile='b/%s' % f
                )
            sys.stderr.writelines(diff)
        if args.writefiles:
            print('updated %s' % f)
        if warnings:
            for warnline in warnings:
                print('warning: %s' % warnline)
