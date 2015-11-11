try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
  name="faunadb",
  description="FaunaDB Python client",
  author="FaunaDB",
  author_email="priority@faunadb.com",
  url="github.com/faunadb/faunadb-python",
  version=0,
  install_requires=["requests"],
  tests_require=["nose", "pynt", "sphinx", "sphinx_rtd_theme", "testfixtures"],
  packages=["faunadb"],
  scripts=[],
  license="MPL 2.0",
  classifiers=[
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5"
  ])
