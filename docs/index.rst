Index
=====

Python client for `FaunaDB <https://faunadb.com>`_.


Installation / Getting Started
------------------------------

Please see the `FaunaDB Documentation <https://faunadb.com/documentation>`_
for information on FaunaDB itself.


Compatibility
-------------

Tested in python 2.7.


Basic Usage
-----------

The first step for any program is to create a :doc:`client` instance.
This object must be explicitly threaded through any code that needs to access FaunaDB.

FaunaDB can be used directly using the :doc:`query` API.

Optionally, :doc:`model` allows database instances
to be represented as objects rather than as dicts.


.. toctree::
   :hidden:

   client
   query
   objects
   page
   model
   errors
