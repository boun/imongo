imongo
======

A MongoDB kernel for Jupyter Lab. Mainly for educational purposes.

This kernel wraps the Mongo shell using pexpect_ and leaves the heavy lifting to metakernel_. It is heavily based on iMongo_ by Gustavo Bezerra.

TODO: Change to more metakernel infrastructure as https://github.com/Jaesin/psysh_kernel/blob/master/psysh_kernel/kernel.py
doc; https://github.com/Calysto/metakernel/blob/master/metakernel/replwrap.py

.. _pexpect: https://github.com/pexpect/pexpect
.. _metakernel: https://github.com/Calysto/metakernel/
.. _iMongo: https://github.com/gusutabopb/imongo

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

Install Jupyter and IMongo Kernel using ``pip``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install Jupyter, this IMongo Kernel and all other dependencies, use ``pip install``:

.. code:: bash

    $ git+https://github.com/boun/imongo#egg=imongo-kernel

TODO:
-----

-  Implement code completion functionality
-  Fix long command issue
-  Send Mongo shell Javascript errors/exceptions to stderr

Acknowledgments:
-----
A part of this work was supported by the European Social Fund

.. figure:: images/esf_logo.png
.. figure:: images/vhb_logo.png
