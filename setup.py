try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
  "description": "FaunaDB Python client",
  "author": "FaunaDB",
  "url": "github.com/faunadb/faunadb-python",
  "version": "0",
  "install_requires": ["requests"],
  "tests_require": ["nose", "pynt", "StringGenerator"],
  "packages": ["faunadb"],
  "scripts": [],
  "name": "faunadb"
}

setup(**config)
