Quick Start Guide
==================

This guide will help you get thinFTP up and running quickly.

Basic Usage
-----------

Here's how to start a basic FTP server:

.. code-block:: python

    from thinftp.server import ThreadedThinFTP, ThinFTP
    from thinftp.logger import get_logger
    from argparse import Namespace
    
    # Create configuration
    config = Namespace(
        bind='localhost',
        port=2121,
        user='anonymous',
        pswd='',
        directory='.',
        lgr=get_logger()
    )
    
    # Create and start the server
    with ThreadedThinFTP((config.bind, config.port), ThinFTP, config) as server:
        server.serve_forever()

Command Line Usage
------------------

You can also run thinFTP from the command line using main.py:

.. code-block:: bash

    thinftp --bind localhost --port 2121 --directory /path/to/ftp/root --user testuser

Connecting to the Server
------------------------

Once the server is running, you can connect using any FTP client:

.. code-block:: bash

    ftp localhost 2121

Or using a GUI FTP client like FileZilla:

* Host: localhost
* Port: 2121
* Username: (leave empty for anonymous)
* Password: (leave empty for anonymous)

Basic Configuration
-------------------

You can customize the server behavior:

.. code-block:: python

    from thinftp.server import ThreadedThinFTP, ThinFTP, start_server
    from thinftp.logger import get_logger
    from argparse import Namespace
    
    # Create custom configuration
    config = Namespace(
        bind='0.0.0.0',        # Listen on all interfaces
        port=2121,
        user='testuser',
        pswd='testpass',
        directory='/home/ftp',   # Custom FTP root directory
        lgr=get_logger(debug=True)  # Enable debug logging
    )
    
    # Start the server
    start_server(config)

Stopping the Server
-------------------

To stop the server gracefully:

.. code-block:: python

    server.stop()

Or use Ctrl+C in the terminal.

