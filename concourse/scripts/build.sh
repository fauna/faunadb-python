#!/bin/sh

set -eou

cd ./fauna-python-repository

python setup.py bdist_wheel --universal
