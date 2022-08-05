[![pylint](https://github.com/zerwes/ansible-fqcn-converter/actions/workflows/pylint.yml/badge.svg)](https://github.com/zerwes/ansible-fqcn-converter/actions/workflows/pylint.yml)

# ansible-fqcn-converter
ansible fqcn converter: update ansible tasks, playbooks etc. to use fully qualified collection name in playbooks (even for ansible buildins)



## usage
```
usage: fqcn-fixer.py [-h] [-d DIRECTORY] [-e FILEEXTENSIONS [FILEEXTENSIONS ...]] [--exclude EXCLUDE_PATHS [EXCLUDE_PATHS ...]]
                     [-c CONFIG] [-w] [-b BACKUPEXTENSION] [-x] [-m FQCNMAPFILE] [-u]

simple script to fix the fqcn module names

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        directory to search files (default: current directory)
  -e FILEEXTENSIONS [FILEEXTENSIONS ...], --extensions FILEEXTENSIONS [FILEEXTENSIONS ...]
                        list of file extensions to use (default: 'yml', 'yaml')
  --exclude EXCLUDE_PATHS [EXCLUDE_PATHS ...]
                        path(s) to directories or files to skip.
  -c CONFIG, --config CONFIG
                        read some cfg args from this file (.ansible-lint can be used)
  -w, --write-files     write back changed files
  -b BACKUPEXTENSION, --backup-extension BACKUPEXTENSION
                        backup extension to use (default: .bak)
  -x, --no-diff         do not print a diff after parsing a file (default: print it)
  -m FQCNMAPFILE, --fqcn-map-file FQCNMAPFILE
                        yaml file to use for the fqcn map (default: /home/zerwes/git/ansible-fqcn-converter/fqcn.yml)
  -u, --update-fqcn-map-file
                        update the fqcn-map-file
```

## notes

### collections
The script uses all collections installed (in the current directory) to build a translation map (aka. `fqcn-map-file`).
If the file is not found (or `--update-fqcn-map-file` is in use), the file defined by `--fqcn-map-file` will be created.

| :warning:     | this wounds time      |
|---------------|:----------------------|

### exclude paths
You can use a `.ansible-lint` config file as input to `-c` in order to define `EXCLUDE_PATHS`
