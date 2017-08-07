.PHONY: build test clean dist release

test:
	pytest --cov thunderstorm_auth --cov-report xml --junit-xml=results.xml test/

build:
	pip install -e .

clean:
	rm -rf dist

dist: clean
	python setup.py sdist

release: dist
	git tag v$$(python setup.py --version)
	git push --tags
	github-release release \
		--user artsalliancemedia \
		--repo thunderstorm-auth-library \
		--tag v$$(python setup.py --version) \
		--pre-release
	github-release upload \
		--user artsalliancemedia \
		--repo thunderstorm-auth-library \
		--tag v$$(python setup.py --version) \
		--name thunderstorm-auth-lib-$$(python setup.py --version).tar.gz \
		--file dist/thunderstorm-auth-lib-$$(python setup.py --version).tar.gz
