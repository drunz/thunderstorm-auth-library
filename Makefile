.PHONY: install lint test build clean dist release codacy


CODACY_PROJECT_TOKEN?=fake
PYTHON_VERSION?=default
REGISTRY?=docker.io
VERSION?=0.0.0

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

lint:
	flake8 thunderstorm_auth test

test: lint
	pytest \
	  -vv \
		--cov thunderstorm_auth \
		--cov-report xml \
		--cov-append \
		--junit-xml results-${PYTHON_VERSION}.xml \
		test/

build:
	pip install -e .

clean:
	rm -rf dist

dist: clean
	python setup.py sdist

codacy: test
	python-codacy-coverage -r coverage.xml
