Installation
============

Requirements
------------

* Python 3.11 or higher
* No external dependencies required

Install from PyPI
-----------------

The easiest way to install thinFTP is using pip:

.. code-block:: bash

    pip install thinftp

Install from Source
-------------------

You can also install thinFTP from source:

.. code-block:: bash

    git clone https://github.com/harishtpj/thinftp.git
    cd thinftp
    pip install -e .

Development Installation
------------------------

For development, install with documentation dependencies:

.. code-block:: bash

    git clone https://github.com/harishtpj/thinftp.git
    cd thinftp
    pip install -e ".[docs]"

Verify Installation
-------------------

To verify that thinFTP is installed correctly:

.. code-block:: python

    import thinftp
    print(thinftp.__version__)

