#! /usr/bin/env python3
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent

import sys
import subprocess
import argparse
import json
import re
from fileinput import FileInput
import difflib

__doc__ = """
simple script to update the fix the fqcn module names
"""

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

files = ['test1.yml', 'test2.yml']
for f in files:
    print('parsing file %s ' % f, file=sys.stderr, end='', flush=True)
    with FileInput(f,
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
                print(nline)
            if args.printdiff:
                changedlines.append(nline)
        print('', file=sys.stderr)
        if args.printdiff:
            diff = difflib.unified_diff(originallines, changedlines, fromfile='a/%s' % f, tofile='b/%s' % f)
            if diff:
                sys.stderr.writelines(diff)
