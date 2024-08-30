export SHELL = /bin/bash


ansible-collection:
	ansible-galaxy collection install -p .collections/ -r requirements.yml
