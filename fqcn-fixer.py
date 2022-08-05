#! /usr/bin/env python3
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent

import sys
import os
import subprocess
import argparse
import json
import yaml
import re
import fileinput
import difflib
import fnmatch

__doc__ = """
simple script to update the fix the fqcn module names
"""

def isexcluded(path, exclude_paths):
    path = os.path.abspath(path)
    return any(
        path.startswith(ep)
        or
        fnmatch.fnmatch(path, ep)
        for ep in exclude_paths
        )

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

args = argparser.parse_args()

# get a dict of ansible modules
modulespr = subprocess.run(
    ['ansible-doc', '-lj'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check = True
    )

fqdndict = {}
modulesdict = json.loads(modulespr.stdout)
for modname in modulesdict.keys():
    fqdn = modname
    if '.' not in modname:
        fqdn = 'ansible.builtin.%s' % modname
    nonfqdn = fqdn.split('.')[-1]
    fqdndict[nonfqdn] = fqdn
#for s, r in fqdndict.items():
#    print('%s -> %s' % (s, r))

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

# do it
for f in parsefiles:
    print('parsing file %s ' % f, file=sys.stderr, end='', flush=True)
    with fileinput.input(f,
            inplace=args.writefiles,
            backup=args.backupextension) as fi:
        originallines = []
        changedlines = []
        startingwhitespaces = False
        for line in fi:
            print('.', file=sys.stderr, end='', flush=True)
            nline = line
            if args.printdiff:
                originallines.append(line)
            for s, r in fqdndict.items():
                if not startingwhitespaces:
                    nline = re.sub('^(\s*)%s:' % s, '\\1%s:' % r, nline)
                    if nline != line:
                        startingwhitespaces = re.search('^\s*', nline).group()
                else:
                    nline = re.sub('^(%s)%s:' % (startingwhitespaces, s), '\\1%s:' % r, nline)
            if args.writefiles:
                print(nline, end='')
            if args.printdiff:
                changedlines.append(nline)
        print('', file=sys.stderr)
        if args.printdiff:
            diff = difflib.unified_diff(originallines, changedlines, fromfile='a/%s' % f, tofile='b/%s' % f)
            if diff:
                sys.stderr.writelines(diff)
