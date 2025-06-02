Configuration
=============

This page describes how to configure thinFTP for different use cases.

Basic Configuration
-------------------

The server can be configured through constructor parameters:

.. code-block:: python

    from thinftp.server import ThinFTPServer
    
    server = ThinFTPServer(
        host='0.0.0.0',          # Bind to all interfaces
        port=2121,               # Custom port
        root_dir='/var/ftp',     # FTP root directory
        max_connections=10,      # Maximum concurrent connections
        timeout=300              # Connection timeout in seconds
    )

Logging Configuration
---------------------

Configure logging levels and output:

.. code-block:: python

    from thinftp.logger import setup_logger
    
    # Setup logger with custom level
    logger = setup_logger(
        name='thinftp',
        level='DEBUG',
        log_file='ftp_server.log'
    )
    
    server = ThinFTPServer(logger=logger)

Security Considerations
-----------------------

.. warning::
   thinFTP is designed for development and educational purposes. 
   For production use, consider additional security measures:
   
   * Use proper authentication
   * Enable SSL/TLS encryption
   * Implement access controls
   * Regular security audits

