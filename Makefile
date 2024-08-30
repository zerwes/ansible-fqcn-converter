export SHELL = /bin/bash


ansible-collection:
	rm -rf .collections/
	mkdir .collections/
	ansible-galaxy collection install -p .collections/ -r requirements.yml
