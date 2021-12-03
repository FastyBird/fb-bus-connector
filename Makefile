.PHONY: python_qa python_tests python_coverage

all:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs

pylint:
	python -m pip install pylint

mypy:
	python -m pip install mypy

black:
	python -m pip install black

isort:
	python -m pip install isort

python_qa: python_cs python_types python_isort python_black

python_cs: pylint
	pylint **/*.py

python_types: mypy
	mypy **/*.py

python_isort: isort
	isort **/*.py --check

python_black: black
	black **/*.py --check

python_tests:
	python -m unittest

python_coverage:
	coverage run --source=fb_bus_connector_plugin -m unittest
