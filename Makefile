.PHONY: build test

test:
	pytest --cov thunderstorm_auth --cov-report xml --junit-xml=results.xml test/

build:
	pip install -e .
