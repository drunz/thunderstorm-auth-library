.PHONY: install lint test clean dist release codacy


CODACY_PROJECT_TOKEN?=fake
PYTHON_VERSION?=default
# only set if running a backwards compatibility test with marshmallow 2.x.x
COMPAT?=
REGISTRY?=886366864302.dkr.ecr.eu-west-1.amazonaws.com
VERSION?=0.0.0

install:
	@echo "# --pre allows pre releases"
	pip install -f --pre -e .
	pip install -r requirements-dev.txt

compat:
	pip uninstall -y marshmallow
	pip install marshmallow==2.18

lint:
	flake8 thunderstorm_auth test

test: lint
	pytest \
	  -vv \
		--cov thunderstorm_auth \
		--cov-report xml:coverage-${PYTHON_VERSION}${COMPAT}.xml \
		--cov-append \
		--junit-xml results-${PYTHON_VERSION}${COMPAT}.xml \
		test/

clean:
	rm -rf dist

dist: clean
	python setup.py sdist

codacy: test
	python-codacy-coverage -r coverage-${PYTHON_VERSION}${COMPAT}.xml
