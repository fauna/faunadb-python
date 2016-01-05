FaunaDB Python
==============

Python client for `FaunaDB <https://faunadb.com>`_.


Installation
------------

.. code-block:: bash

    $ pip install faunadb


Documentation
-------------

Client documentation is available at https://faunadb.readthedocs.org/en/latest/.

See the `FaunaDB Documentation <https://faunadb.com/documentation>`_ for a complete API reference, or look in `tests`_
for more examples.


Building it yourself
--------------------


Setup
~~~~~

.. code-block:: bash

    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install .
    $ make


Testing
~~~~~~~

To run the tests you must have a FaunaDB database available.
Then set the environment variable ``FAUNA_ROOT_KEY`` to your database's root key.
If you use FaunaDB cloud, this is the password you log in with.

Then run ``make test``.
To test a single test, use e.g. ``python -m unittest tests.test_client.ClientTest.test_ping``.


Documenting
~~~~~~~~~~~

Run ``make docs``, then open ``docs/_build/html/index.html`` in a web browser.


Contribute
----------

GitHub pull requests are very welcome.


License
-------

Copyright 2015 `Fauna, Inc. <https://faunadb.com>`_

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
