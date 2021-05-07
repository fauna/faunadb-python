#!/bin/sh

set -eou

apk add --update make

pip install .
pip install nose2
pip install pylint
make test
