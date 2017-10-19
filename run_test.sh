#!/bin/bash

# This script is used by docker-compose to run tests against different python versions

echo "Install package"
apt-get update && apt-get -y --no-install-recommends install build-essential libffi-dev && apt-get clean && rm -rf /var/lib/apt/lists/*
make build
pip install -r requirements-dev.txt

echo "Run tests"
make test
