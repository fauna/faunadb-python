#!/bin/sh

set -eou

cd ./fauna-python-repository

PACKAGE_VERSION=$(python setup.py --version)
echo "Going to publish python package: ${PACKAGE_VERSION}"

apk --no-progress --no-cache add gcc musl-dev python3-dev libffi-dev openssl-dev cargo

pip install twine

twine check dist/*
twine upload dist/*
