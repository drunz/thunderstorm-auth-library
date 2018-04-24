.PHONY: requirements requirements-dev lint test build clean dist release codacy


CODACY_PROJECT_TOKEN?=fake


requirements:
	pip install -r requirements.txt

requirements-dev: requirements
	pip install -r requirements-dev.txt

lint:
	flake8 thunderstorm_auth test

test: lint
	pytest \
		--cov thunderstorm_auth \
		--cov-report xml \
		--junit-xml test_results/results.xml \
		test/

build:
	pip install -e .

clean:
	rm -rf dist

dist: clean
	python setup.py sdist

codacy: test
	python-codacy-coverage -r coverage.xml
