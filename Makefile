.PHONY: build test

test:
	pytest --cov thunderstorm_auth test/

build:
	pip install -e .
