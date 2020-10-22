from setuptools import setup
from codecs import open
from os import path
from faunadb import __version__ as pkg_version, __author__ as pkg_author, __license__ as pkg_license

# Load the README file for use in the long description
local_dir = path.abspath(path.dirname(__file__))
with open(path.join(local_dir, "README.rst"), encoding="utf-8") as f:
  long_description = f.read()

requires = [
  "iso8601",
  "requests",
  "future",
  "hyper"
]

tests_requires = [
  "nose2",
  "nose2[coverage_plugin]",
]

extras_require = {
  "doc": ["sphinx", "sphinx_rtd_theme"],
  "test": tests_requires,
  "lint": ["pylint"],
}

setup(
  name="faunadb",
  version=pkg_version,
  description="FaunaDB Python driver",
  long_description=long_description,
  url="https://github.com/fauna/faunadb-python",
  author=pkg_author,
  author_email="priority@fauna.com",
  license=pkg_license,
  classifiers=[
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
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
  tests_require=tests_requires,
  test_suite="nose2.collector.collector",
)
