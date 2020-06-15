help:
	@echo Look at the Makefile


createvenv:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt 

