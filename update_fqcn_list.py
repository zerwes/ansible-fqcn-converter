#! /usr/bin/env python3
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent

import os
import sys
import argparse
import logging
import hiyapyco
import requests

__doc__ = """
simple script to update the fqcn list
"""

logger = logging.getLogger()
logging.basicConfig(
    level=logging.WARN,
    format='%(levelname)s\t[%(name)s] %(funcName)s: %(message)s'
    )

argparser = argparse.ArgumentParser(description=__doc__)
argparser.add_argument(
    '-c', '--config-files',
    type=str, nargs='+',
    dest='configfiles',
    default=['config.yml',],
    help='list of config files to use'
    )
argparser.add_argument(
    '-o', '--out-file',
    type=str,
    dest='outfile', action='store',
    default='fqcnmap.yml',
    help="file to store the fqcn translation map"
    )

args = argparser.parse_args()

logger.warning('reading config files: %s', ', '.join(args.configfiles))
conf = hiyapyco.load(
    *args.configfiles,
    method=hiyapyco.METHOD_MERGE,
    interpolate=True,
    failonmissingfiles=True,
    )

for org in conf['github_collections_list']:
    url = 'https://api.github.com/orgs/%s/repos' % org
    logger.warning('reading repos from %s', url)
    response = requests.get(url)
    assert response.status_code == 200
    response_d = response.json()
    print(response_d)
