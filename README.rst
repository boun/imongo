imongo
======

A MongoDB kernel for Jupyter Lab. Mainly for educational purposes.

This kernel wraps the Mongo shell using pexpect_ and leaves the heavy lifting to metakernel_. It is heavily based on iMongo_ by Gustavo Bezerra.

.. _pexpect: https://github.com/pexpect/pexpect
.. _metakernel: https://github.com/Calysto/metakernel/
.. _iMongo: https://github.com/Calysto/metakernel/

.. figure:: screenshot.png
   :alt: IMongo in action

   IMongo in action

How to install
--------------

Major requirements
~~~~~~~~~~~~~~~~~~

IMongo requires Jupyter_ and MongoDB_.

.. _Jupyter: http://jupyter.org
.. _MongoDB: https://www.mongodb.com

Install MongoDB
^^^^^^^^^^^^^^^

On macOS, use Homebrew_: ``brew install mongodb``

For other platforms, please refer to the MongoDB documentation_

.. _Homebrew: http://brew.sh/
.. _documentation: https://docs.mongodb.com/manual/installation/

Install Jupyter and IMongo Kernel using ``pip``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install Jupyter, IMongo and all other dependencies, use ``pip install``:

.. code:: bash

    $ pip install imongo-kernel

TODO:
-----

-  Implement code completion functionality
-  Fix long command issue
-  Send Mongo shell Javascript errors/exceptions to stderr
