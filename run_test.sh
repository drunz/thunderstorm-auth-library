#!/bin/bash


echo "Install package"
pip install -e .

echo "Run tests"
pytest --cov thunderstorm_auth test/
