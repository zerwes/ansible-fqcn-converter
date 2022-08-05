#! /usr/bin/env python3
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent

import subprocess
import argparse
import json

__doc__ = """
simple script to update the fqcn list
"""

argparser = argparse.ArgumentParser(description=__doc__)
argparser.add_argument(
    '-o', '--out-file',
    type=str,
    dest='outfile', action='store',
    default='fqcnmap.yml',
    help="file to store the fqcn translation map"
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
print(fqdndict)
