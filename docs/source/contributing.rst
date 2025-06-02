Contributing
============

We welcome contributions to thinFTP! This guide will help you get started.

Development Setup
-----------------

1. Fork the repository on GitHub
2. Clone your fork locally:

.. code-block:: bash

    git clone https://github.com/yourusername/thinftp.git
    cd thinftp

3. Install in development mode:

.. code-block:: bash

    pip install -e ".[docs]"

Running Tests
-------------

.. code-block:: bash

    python -m pytest tests/

Building Documentation
----------------------

To build the documentation locally:

.. code-block:: bash

    cd docs
    make html

The built documentation will be in `docs/build/html/`.

Code Style
----------

* Follow PEP 8 style guidelines
* Use type hints where appropriate
* Write clear, descriptive docstrings
* Keep functions and classes focused and small

Submitting Changes
------------------

1. Create a new branch for your feature:

.. code-block:: bash

    git checkout -b feature/your-feature-name

2. Make your changes and add tests
3. Ensure all tests pass
4. Update documentation if needed
5. Commit your changes:

.. code-block:: bash

    git commit -m "Add your feature description"

6. Push to your fork and submit a pull request

Reporting Issues
----------------

When reporting issues, please include:

* Python version
* Operating system
* Clear description of the problem
* Steps to reproduce
* Any error messages or logs

License
-------

By contributing, you agree that your contributions will be licensed under the MIT License.

