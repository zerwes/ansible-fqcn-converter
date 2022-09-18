[![pylint](https://github.com/zerwes/ansible-fqcn-converter/actions/workflows/pylint.yml/badge.svg)](https://github.com/zerwes/ansible-fqcn-converter/actions/workflows/pylint.yml)
[![test](https://github.com/zerwes/ansible-fqcn-converter/actions/workflows/test.yml/badge.svg)](https://github.com/zerwes/ansible-fqcn-converter/actions/workflows/test.yml)

# Ansible FQCN converter
Update ansible tasks, playbooks, handlers etc. to use fully qualified module names (even for ansible buildins) by searching for all known modules that are not in fqcn notation and replacing them with the fqcn name.
In some cases the replacement might be ambiguous, so a warning will be printed (and by default added as a comment to the changed files).

Tha ansible files should be linted and valid yaml files. Esp. the following ansible-lint tags should be covered:
 - no-tabs
 - yaml
 
## HowTo
 1. Clone this repo to a convenient place: `git clone https://github.com/zerwes/ansible-fqcn-converter.git`

 2. Ensure the python script is executable: `chmod 755 ansible-fqcn-converter/fqcn-fixer.py`

 3. Optional: re-create the `fqcn-map-file` (:warning: takes about 40 minutes :warning:): `./ansible-fqcn-converter/fqcn-fixer.py --update-fqcn-map-file`

 4. Optional: Go to the desired directory containing the ansible roles/playbooks etc. and execute: `ansible-lint .` and ensure the yaml syntax ist OK

 5. Go to the desired directory containing the ansible roles/playbooks etc. and execute: `$PATH_TO_ansible-fqcn-converter/fqcn-fixer.py`

 6. If the diff displayed seems OK to you, let the script modify your files (:exclamation: use at your own risk :exclamation:): `$PATH_TO_ansible-fqcn-converter/fqcn-fixer.py -w`

 7. Run the latest `ansible-lint .` and enjoy missing the `Error: fqcn-builtins Use FQCN for builtin actions.`

## usage
```
usage: fqcn-fixer.py [-h] [-d DIRECTORY] [-e FILEEXTENSIONS [FILEEXTENSIONS ...]]
                     [--exclude EXCLUDE_PATHS [EXCLUDE_PATHS ...]] [--do-not-use-default-exclude]
                     [-c CONFIG] [-w] [-W] [-b BACKUPEXTENSION] [-x] [-m FQCNMAPFILE] [-u]

simple script to fix the fqcn module names

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        directory to search files (default: current directory)
  -e FILEEXTENSIONS [FILEEXTENSIONS ...], --extensions FILEEXTENSIONS [FILEEXTENSIONS ...]
                        list of file extensions to use (default: 'yml', 'yaml')
  --exclude EXCLUDE_PATHS [EXCLUDE_PATHS ...]
                        path(s) to directories or files to skip.
  -f FILTER_PATH, --filter FILTER_PATH
                        path(s)/file(s) to limit processing to.
  --do-not-use-default-exclude
                        do not use the default excludes
  -c CONFIG, --config CONFIG
                        read some cfg args from this file (.ansible-lint can be used)
  -w, --write-files     write back changed files
  -W, --no-write-warnings
                        do not write warnings as comments to files and diff
  -b BACKUPEXTENSION, --backup-extension BACKUPEXTENSION
                        backup extension to use (default: .bak)
  -x, --no-diff         do not print a diff after parsing a file (default: print it)
  -m FQCNMAPFILE, --fqcn-map-file FQCNMAPFILE
                        yaml file to use for the fqcn map
                        (default: fqcn.yml in the directory of the script)
  -u, --update-fqcn-map-file
                        update the fqcn-map-file
```

## caveats
  * :warning: you should exclude VAR files, molecule and other CI/CD files etc.

## notes

### collections
The script uses all collections installed (in the current directory) to build a translation map (aka. `fqcn-map-file`).

If the file is not found (or `--update-fqcn-map-file` is in use), the file defined by `--fqcn-map-file` will be created. (:warning: **this wounds time** :warning:)

### exclude paths
You can use a `.ansible-lint` config file as input to `-c` in order to define `EXCLUDE_PATHS`

### tricks
parse just one file: use `-e $FILENAME`

## example
Example result from [ansible-opnsense-checkmk](https://github.com/Rosa-Luxemburgstiftung-Berlin/ansible-opnsense-checkmk): [commit ffb281e67511c3c729661e8bbd3ca460b8c3d190](https://github.com/Rosa-Luxemburgstiftung-Berlin/ansible-opnsense-checkmk/commit/ffb281e67511c3c729661e8bbd3ca460b8c3d190)

```diff
commit ffb281e67511c3c729661e8bbd3ca460b8c3d190
Author: Klaus Zerwes <zerwes@users.noreply.github.com>
Date:   Fri Aug 5 22:42:16 2022 +0200

    applied changes using https://github.com/zerwes/ansible-fqcn-converter/blob/main/fqcn-fixer.py

diff --git a/handlers/main.yml b/handlers/main.yml
index 4757041..03970f4 100644
--- a/handlers/main.yml
+++ b/handlers/main.yml
@@ -1,7 +1,7 @@
 ---
 
 - name: service inetd
-  service:
+  ansible.builtin.service:
     name: inetd
     state: restarted
 
diff --git a/tasks/main.yml b/tasks/main.yml
index d9885ca..dca0b0c 100644
--- a/tasks/main.yml
+++ b/tasks/main.yml
@@ -1,11 +1,11 @@
 ---
 - name: Install opnsense packages
-  pkgng:
+  community.general.pkgng:
     name: "{{ opn_packages }}"
     state: present
 
 - name: copy check_mk_agent
-  copy:
+  ansible.builtin.copy:
     src: check_mk_agent.freebsd
     dest: "{{ opn_check_mk_path }}"
     mode: 0700
@@ -13,7 +13,7 @@
   when: opn_install_check_mk
 
 - name: create lib dirs
-  file:
+  ansible.builtin.file:
     path: "{{ opn_check_mk_lib_dir }}/{{ item }}"
     state: directory
     mode: 0755
@@ -23,7 +23,7 @@
   when: opn_install_check_mk
 
 - name: copy check_mk plugins
-  copy:
+  ansible.builtin.copy:
     src: "{{ item }}"
     dest: "{{ opn_check_mk_lib_dir }}/plugins/{{ item }}"
     mode: 0700
@@ -31,7 +31,7 @@
   when: opn_install_check_mk
 
 - name: copy check_mk local checks
-  copy:
+  ansible.builtin.copy:
     src: "{{ item }}"
     dest: "{{ opn_check_mk_lib_dir }}/local/{{ item }}"
     mode: 0700
@@ -39,7 +39,7 @@
   when: opn_install_check_mk
 
 - name: copy check_mk additional files
-  copy:
+  ansible.builtin.copy:
     src: "{{ item.key }}"
     dest: "{{ item.value }}"
     mode: 0600
@@ -47,7 +47,7 @@
   when: opn_install_check_mk
 
 - name: enable check_mk_agent in /etc/inetd.conf
-  lineinfile:
+  ansible.builtin.lineinfile:
     path: /etc/inetd.conf
     line: "check_mk  stream  tcp nowait  root  {{ opn_check_mk_path }} {{ opn_check_mk_path | basename }}"
     regexp: "^check_mk "
@@ -55,7 +55,7 @@
   when: opn_install_check_mk
 
 - name: add service to /etc/services
-  lineinfile:
+  ansible.builtin.lineinfile:
     path: /etc/services
     line: "check_mk	{{ opn_check_mk_port }}/tcp   #check_mk agent"  # noqa no-tabs
     regexp: "^check_mk "
@@ -63,7 +63,7 @@
   when: opn_install_check_mk
 
 - name: setup /etc/hosts.allow
-  lineinfile:
+  ansible.builtin.lineinfile:
     path: /etc/hosts.allow
     line: "check_mk	: {{ checkmk_ip }} : allow"  # noqa no-tabs
     regexp: "^check_mk "
@@ -71,12 +71,12 @@
   when: opn_install_check_mk
 
 - name: debug ansible_local
-  debug:
+  ansible.builtin.debug:
     var: ansible_local
     verbosity: 1
 
 - name: enable inetd
-  blockinfile:
+  ansible.builtin.blockinfile:
     backup: true
     path: /etc/rc.conf
     block: |
@@ -87,7 +87,7 @@
   notify: service inetd
 
 - name: enable inetd
-  blockinfile:
+  ansible.builtin.blockinfile:
     backup: true
     path: /etc/rc.conf.d/inetd
     create: true
```
