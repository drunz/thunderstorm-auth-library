#!/bin/bash

# This script is used by docker-compose to run tests against different python versions

echo "Install package"
pip install -e .

echo "Run tests"
pytest --cov thunderstorm_auth --cov-report xml --junit-xml=results.xml test/
