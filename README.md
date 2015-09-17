# faunadb-python

Python client for [FaunaDB](https://faunadb.com).

Documentation is [here](https://faunadb.readthedocs.org/en/latest/).

See the [FaunaDB Documentation](https://faunadb.com/documentation) for
a complete API reference, or look in
[`/tests`](https://github.com/faunadb/faunadb-python/tree/master/tests) for more
examples.


## Building it yourself

### Setup

  virtualenv venv
  source venv/bin/activate
  pip install .
  pynt

### Testing

To run the tests you must have a FaunaDB database available.
Then set the environment variable `FAUNA_ROOT_KEY` to your database's root key.
If you use FaunaDB cloud, this is the password you log in with.

Then run `pynt test`.
To test a single test, use e.g. `nosetests tests/client_test.py:ClientTest.test_ping`.

### Documenting

Run `pynt document`, then open `docs/_build/html/index.html` in a web browser.


## Contributing

GitHub pull requests are very welcome.


## LICENSE

Copyright 2015 [Fauna, Inc.](https://faunadb.com/)

Licensed under the Mozilla Public License, Version 2.0 (the
"License"); you may not use this software except in compliance with
the License. You may obtain a copy of the License at

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing
permissions and limitations under the License.
