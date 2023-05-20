#! /bin/bash

declare -i E=0

cd $(dirname $0)

cp example.yml example.yml.orig

./fqcn-fixer.py -c examplecfg.yml -f example.yml -w -x -W

cmp example.yml exampleconverted.yml
E=$?

if [ $E -gt 0 ]; then
	diff -Naur example.yml exampleconverted.yml
	echo -e "\n\tERROR: conversion not as expected\n"
else
	echo -e "\n\tconversion successful\n"
fi

mv example.yml.orig example.yml

exit $E
