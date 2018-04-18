#!/bin/bash

# This script is used by tox container to install requirements

apt-get update \
    && apt-get -y --no-install-recommends install build-essential libffi-dev git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
