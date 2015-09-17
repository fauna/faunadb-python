FaunaDB
=======

Python client for `FaunaDB <https://faunadb.com>`_.


Installation / Getting Started
------------------------------

To install, run :samp:`pip install faunadb`.

Please see the `FaunaDB Documentation <https://faunadb.com/documentation>`_
for information on FaunaDB itself.


Compatibility
-------------

Should work in python 2.6+ and 3.1+.


Basic Usage
-----------

The first step for any program is to create a :doc:`client` instance.
This object must be explicitly threaded through any code that needs to access FaunaDB.

FaunaDB can be used directly using the :doc:`query` API.


.. toctree::
   :hidden:

   client
   query
   objects
   errors
