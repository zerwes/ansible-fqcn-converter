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
import yaml

__doc__ = """
simple script to fix the fqcn module names
"""

def isexcluded(path, _exclude_paths):
    """check if a path element should be excluded"""
    path = os.path.abspath(path)
    return any(
        path.startswith(ep)
        or
        fnmatch.fnmatch(path, ep)
        for ep in _exclude_paths
        )

basepath = os.path.dirname(os.path.realpath(__file__))

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

args = argparser.parse_args()

# get a dict of ansible modules
fqdndict = {}
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
    modjson = json.loads(modpr.stdout)
    moddict = modjson[modname]
    if 'doc' in moddict and 'collection' in moddict['doc'] and 'module' in moddict['doc']:
        fqdn = '%s.%s' % (moddict['doc']['collection'], moddict['doc']['module'])
        nonfqdn = fqdn.split('.')[-1]
        fqdndict[nonfqdn] = fqdn
for s, r in fqdndict.items():
    print('%s -> %s' % (s, r))
sys.exit()

# build exclude_paths
exclude_paths = []
for ep in args.exclude_paths + [".cache", ".git", ".hg", ".svn", ".tox"]:
    exclude_paths.append(os.path.abspath(ep))

# update some args from optional config file
config = False
if args.config:
    try:
        with open(args.config) as ymlfile:
            config = yaml.load(ymlfile, Loader=yaml.BaseLoader)
    except FileNotFoundError:
        pass
if config and config['exclude_paths']:
    for ep in config['exclude_paths']:
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
_fqcnregex = re.compile(r'^(?P<white>\s*)(?P<module>%s):' % '|'.join(fqdndict.keys()))

# do it
for f in parsefiles:
    print('parsing file %s ' % f, file=sys.stderr, end='', flush=True)
    with fileinput.input(f,
            inplace=args.writefiles,
            backup=args.backupextension) as fi:
        originallines = []
        changedlines = []
        startingwhitespaces = False
        fqcnregex = _fqcnregex
        for line in fi:
            print('.', file=sys.stderr, end='', flush=True)
            if args.printdiff:
                originallines.append(line)
            nline = line
            fqcnmatch = fqcnregex.match(line)
            if fqcnmatch:
                if not startingwhitespaces:
                    startingwhitespaces = fqcnmatch.group('white')
                    fqcnregex = re.compile('^%s(?P<module>%s):' %
                        (startingwhitespaces, '|'.join(fqdndict.keys()))
                        )
                fqcnmodule = fqcnmatch.group('module')
                nline = re.sub(
                    '^(%s)%s:' % (startingwhitespaces, fqcnmodule),
                    '\\1%s:' % fqdndict[fqcnmodule],
                    line
                    )
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
