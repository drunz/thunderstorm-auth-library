.PHONY: build test clean dist

test:
	pytest --cov thunderstorm_auth --cov-report xml --junit-xml=results.xml test/

build:
	pip install -e .

clean:
	rm -rf dist

dist: clean
	python setup.py sdist
