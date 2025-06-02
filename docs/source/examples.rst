Examples
========

Here are some practical examples of using thinFTP.

Basic FTP Server
----------------

.. code-block:: python

    from thinftp.server import start_server
    from thinftp.logger import get_logger
    from argparse import Namespace
    
    # Simple FTP server configuration
    config = Namespace(
        bind='localhost',
        port=2121,
        user='anonymous',
        pswd='',
        directory='.',
        lgr=get_logger()
    )
    
    # Start the server
    start_server(config)

Custom Root Directory
---------------------

.. code-block:: python

    import os
    from thinftp.server import start_server
    from thinftp.logger import get_logger
    from argparse import Namespace
    
    # Create FTP root directory if it doesn't exist
    ftp_root = os.path.expanduser("~/ftp_files")
    os.makedirs(ftp_root, exist_ok=True)
    
    config = Namespace(
        bind='localhost',
        port=2121,
        user='testuser',
        pswd='testpass',
        directory=ftp_root,
        lgr=get_logger()
    )
    start_server(config)

With Custom Logging
-------------------

.. code-block:: python

    from thinftp.server import start_server
    from thinftp.logger import get_logger
    from argparse import Namespace
    
    # Setup detailed logging
    logger = get_logger(debug=True)
    
    config = Namespace(
        bind='0.0.0.0',
        port=8021,
        user='ftpuser',
        pswd='ftppass',
        directory='.',
        lgr=logger
    )
    
    print("Starting FTP server with debug logging...")
    start_server(config)

Command Line Examples
---------------------

.. code-block:: bash

    # Basic server
    thinftp --bind localhost --port 2121 --user anonymous
    
    # Custom directory and debug logging
    thinftp --bind 0.0.0.0 --port 8021 --directory /home/ftp --user ftpuser --debug
    
    # Different port
    thinftp --port 2525 --user testuser

