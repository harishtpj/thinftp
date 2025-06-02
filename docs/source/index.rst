thinFTP Documentation
=====================

A minimal, lightweight FTP server implementation in Python.

.. note::
   thinFTP is designed to be a simple, educational FTP server. It's perfect for 
   learning about FTP protocols or for lightweight development scenarios.

Quick Start
-----------

Install thinFTP:

.. code-block:: bash

   pip install thinftp

Run the server:

.. code-block:: bash

   thinftp --bind localhost --port 2121 --user testuser

Or programmatically:

.. code-block:: python

   from thinftp.server import start_server
   from thinftp.logger import get_logger  
   from argparse import Namespace
   
   config = Namespace(
       bind='localhost', port=2121, user='anonymous', 
       pswd='', directory='.', lgr=get_logger()
   )
   start_server(config)

Features
--------

* 🚀 **Lightweight**: Minimal dependencies and footprint
* 📝 **Well-documented**: Comprehensive documentation with examples
* 🔧 **Configurable**: Easy to customize and extend
* 🐍 **Pure Python**: No external dependencies required
* 📋 **FTP Compliant**: Implements standard FTP protocol

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   
   installation
   quickstart
   configuration
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   
   api/server
   api/handler
   api/fileman
   api/logger
   api/errors

.. toctree::
   :maxdepth: 1
   :caption: Development
   
   contributing
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
