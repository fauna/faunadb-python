#!/bin/sh

set -eou

cd ./fauna-python-repository

PACKAGE_VERSION=$(python setup.py --version)

apk --no-progress --no-cache add gcc musl-dev python3-dev libffi-dev openssl-dev cargo

pip install .
pip install pdoc3
pdoc faunadb --html -o docs

cd ../
mkdir docs
cp -R ./fauna-python-repository/docs/faunadb/* ./docs/

echo "Current docs version: $PACKAGE_VERSION"

apk add --no-progress --no-cache sed

echo "================================="
echo "Adding google manager tag to head"
echo "================================="

HEAD_GTM=$(cat ./fauna-python-repository/concourse/scripts/head_gtm.dat)
sed -i.bak "0,/<\/title>/{s/<\/title>/<\/title>${HEAD_GTM}/}" ./docs/index.html

echo "================================="
echo "Adding google manager tag to body"
echo "================================="

BODY_GTM=$(cat ./fauna-python-repository/concourse/scripts/body_gtm.dat)
sed -i.bak "0,/<body>/{s/<body>/<body>${BODY_GTM}/}" ./docs/index.html

rm ./docs/index.html.bak

apk add --no-progress --no-cache git
git clone fauna-python-repository-docs fauna-python-repository-updated-docs

cd fauna-python-repository-updated-docs

rm -rf ./api/*
cp -R ../docs/* ./api/

git config --global user.email "nobody@fauna.com"
git config --global user.name "Fauna, Inc"

git add -A
git commit -m "Update docs to version: $PACKAGE_VERSION"
