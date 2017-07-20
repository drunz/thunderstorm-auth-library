#!/bin/bash


echo "Install package"
pip install -e .

echo "Run tests"
pytest --cov thunderstorm_auth --cov-report xml --junit-xml=results.xml test/
