FaunaDB Python
==============

WIP
---

This driver is under development. Changes may happen until we have an official release

.. image:: https://img.shields.io/travis/faunadb/faunadb-python/master.svg?maxAge=21600
 :target: https://travis-ci.org/faunadb/faunadb-python
.. image:: https://img.shields.io/codecov/c/github/faunadb/faunadb-python/master.svg?maxAge=21600
 :target: https://codecov.io/gh/faunadb/faunadb-python
.. image:: https://img.shields.io/pypi/v/faunadb.svg?maxAge=21600
 :target: https://pypi.python.org/pypi/faunadb
.. image:: https://img.shields.io/badge/license-MPL_2.0-blue.svg?maxAge=2592000
 :target: https://raw.githubusercontent.com/faunadb/faunadb-python/master/LICENSE

Python driver for `FaunaDB <https://fauna.com>`_.


Installation
------------

.. code-block:: bash

    $ pip install faunadb


Compatibility
-------------

The following versions of Python are supported:

* Python 2.7
* Python 3.3
* Python 3.4
* Python 3.5


Documentation
-------------

Driver documentation is available at https://pythonhosted.org/faunadb/.

See the `FaunaDB Documentation <https://fauna.com/documentation>`_ for a complete API reference, or look in `tests`_
for more examples.


Basic Usage
-----------

The first step for any program is to create a ``client`` instance.
This object must be explicitly threaded through any code that needs to access FaunaDB.

FaunaDB can be used directly using the ``query`` API.


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

Then run ``make test``.
To test a single test, use e.g. ``python -m unittest tests.test_client.ClientTest.test_ping``.


Coverage
~~~~~~~~

To run the tests with coverage, install the coverage dependencies with ``pip install .[coverage]``,
and then run ``make coverage``. A summary will be displayed to the terminal, and a detailed coverage report
will be available at ``htmlcov/index.html``.


Documenting
~~~~~~~~~~~

Run ``pip install .[doc]`` to install the needed packages to generate the docs.
Then run ``make doc``, then open ``docs/_build/html/index.html`` in a web browser.


Contribute
----------

GitHub pull requests are very welcome.


License
-------

Copyright 2016 `Fauna, Inc. <https://fauna.com>`_

Licensed under the Mozilla Public License, Version 2.0 (the
"License"); you may not use this software except in compliance with
the License. You may obtain a copy of the License at

`http://mozilla.org/MPL/2.0/ <http://mozilla.org/MPL/2.0/>`_

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing
permissions and limitations under the License.


.. _`tests`: https://github.com/faunadb/faunadb-python/blob/master/tests/
