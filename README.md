# ansible-fqcn-converter
ansible fqcn converter

## usage
```
usage: fqcn-fixer.py [-h] [-d DIRECTORY] [-e FILEEXTENSIONS [FILEEXTENSIONS ...]] [--exclude EXCLUDE_PATHS [EXCLUDE_PATHS ...]]
                     [-c CONFIG] [-w] [-b BACKUPEXTENSION] [-x]

simple script to update the fix the fqcn module names

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
```

## notes

### collections
the scripts uses all collections installed (in the current directory) to build a translation map

### exclude paths
you can use a `.ansible-lint` config file as input to `-c` in order to define `EXCLUDE_PATHS`
