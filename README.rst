FaunaDB Python
==============

.. image:: https://img.shields.io/codecov/c/github/fauna/faunadb-python/master.svg?maxAge=21600
 :target: https://codecov.io/gh/fauna/faunadb-python
.. image:: https://img.shields.io/pypi/v/faunadb.svg?maxAge=21600
 :target: https://pypi.python.org/pypi/faunadb
.. image:: https://img.shields.io/badge/license-MPL_2.0-blue.svg?maxAge=2592000
 :target: https://raw.githubusercontent.com/fauna/faunadb-python/main/LICENSE

Python driver for `FaunaDB <https://fauna.com>`_.


Installation
------------

.. code-block:: bash

    $ pip install faunadb


Compatibility
-------------

The following versions of Python are supported:

* Python 3.5
* Python 3.6
* Python 3.7
* Python 3.8
* Python 3.9

Documentation
-------------

Driver documentation is available at https://fauna.github.io/faunadb-python/4.1.1/api/.

See the `FaunaDB Documentation <https://docs.fauna.com/>`__ for a complete API reference, or look in `tests`_
for more examples.


Basic Usage
-----------

.. code-block:: python

    from faunadb import query as q
    from faunadb.objects import Ref
    from faunadb.client import FaunaClient

    client = FaunaClient(secret="your-secret-here")

    indexes = client.query(q.paginate(q.indexes()))

    print(indexes)

Document Streaming
------------------
Fauna supports document streaming, where changes to a streamed document are pushed to all clients subscribing to that document.

The following section provides an example for managing a document stream.

The streaming API is blocking by default, the choice and mechanism for handling concurrent streams is left to the application developer:

.. code-block:: python

    from faunadb import query as q
    from faunadb.objects import Ref
    from faunadb.client import FaunaClient

    client = FaunaClient(secret="your-secret-here")

    coll = client.query(q.create_collection({"name":"sc"}))
    doc  = client.query(q.create(coll["ref"], {"data":{"x": 0}}))

    stream = None
    def on_start(event):
        print("started stream at %s"%(event.txn))
        client.query(q.update(doc["ref"], {"data": {"x": "updated"}}))

    def on_version(event):
        print("on_version event at %s"%(event.txn))
        print("    event: %s"%(event.event))
        stream.close()

    def on_error(event):
        print("Received error event %s"%(event))
    options = {"fields": ["document", "diff"]}
    stream = client.stream(doc["ref"], options, on_start, on_error, on_version)
    stream.start()

Observing Metrics
-----------------

Its possible to observe each query's metrics by providing an "observer" callback.

More information on query metrics is available in the `FaunaDB Documentation <https://docs.fauna.com/fauna/current/learn/understanding/billing#perquery>`__.

Here is a simple example:

.. code-block:: python

    from faunadb import query as q
    from faunadb.client import FaunaClient
    from faunadb.errors import FaunaError

    # The observer callback, which takes the HTTP response for a query
    def observe(response):
        h = response.response_headers
        print('bytesOut:', h["x-compute-ops"])
        print('queryTime:', h["x-query-time"])
        print('readOps:', h["x-byte-read-ops"])
        print('writeOps:', h["x-byte-write-ops"])
        print('retries:', h["x-txn-retries"])

    # Connect to a local Fauna Dev instance
    client = FaunaClient(
        secret="secret",
        domain="localhost",
        scheme="http",
        port=8443,
        observer=observe
    )

    try:
        result = client.query(
            q.paginate(q.collections())
        )
    except FaunaError as err:
        print("err: ", err)
    else:
        print(result)

Building it yourself
--------------------


Setup
~~~~~

.. code-block:: bash

    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install .


Testing
~~~~~~~

To run the tests you must have a FaunaDB database available.
Then set the environment variable ``FAUNA_ROOT_KEY`` to your database's root key.
If you use FaunaDB cloud, this is the password you log in with.

Tip: Setting the ``FAUNA_QUERY_TIMEOUT_MS`` environment variable will
set a timeout in milliseconds for all queries.

Then run ``make test``.
To test a single test, use e.g. ``python -m unittest tests.test_client.ClientTest.test_ping``.

Tests can also be run via a Docker container with ``FAUNA_ROOT_KEY="your-cloud-secret" make docker-test``
(an alternate Alpine-based Python image can be provided via `RUNTIME_IMAGE`).


Coverage
~~~~~~~~

To run the tests with coverage, install the coverage dependencies with ``pip install .[coverage]``,
and then run ``make coverage``. A summary will be displayed to the terminal, and a detailed coverage report
will be available at ``htmlcov/index.html``.


Contribute
----------

GitHub pull requests are very welcome.


License
-------

Copyright 2020 `Fauna, Inc. <https://fauna.com>`_

Licensed under the Mozilla Public License, Version 2.0 (the
"License"); you may not use this software except in compliance with
the License. You may obtain a copy of the License at

`http://mozilla.org/MPL/2.0/ <http://mozilla.org/MPL/2.0/>`_

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing
permissions and limitations under the License.


.. _`tests`: https://github.com/fauna/faunadb-python/blob/main/tests/
