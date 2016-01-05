from setuptools import setup
from codecs import open
from os import path
from faunadb import __version__ as version

# Load the README file for use in the long description
local_dir = path.abspath(path.dirname(__file__))
with open(path.join(local_dir, "README.rst"), encoding="utf-8") as f:
  long_description = f.read()

requires = [
  "iso8601",
  "requests"
]

extras_require = {
  "docs": ["sphinx", "sphinx_rtd_theme"],
  "test": ["pylint"]
}

setup(
  name="faunadb",
  version=version,
  description="FaunaDB Python client",
  long_description=long_description,
  url="https://github.com/faunadb/faunadb-python",
  author="FaunaDB",
  author_email="priority@faunadb.com",
  license="MPL 2.0",
  classifiers=[
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    "Programming Language :: Python :: 2 :: Only",
    "Programming Language :: Python :: 2.7",
    "Topic :: Database",
    "Topic :: Database :: Front-Ends",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: Unix",
  ],
  keywords="faunadb fauna",
  packages=["faunadb"],
  install_requires=requires,
  extras_require=extras_require,
  test_suite="tests",
)
