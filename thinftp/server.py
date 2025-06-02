
"""
Server module for thinFTP.

This module defines the threaded TCP server for the FTP service.
It uses Python's built-in `socketserver.ThreadingTCPServer` to
handle multiple client connections concurrently.
"""

import socketserver
from .handler import ThinFTP

class ThreadedThinFTP(socketserver.ThreadingTCPServer):
    """
    A threaded FTP server class for handling multiple client connections.

    Attributes:
        config (Namespace): A configuration object containing server settings.
        lgr (logging.Logger): Logger instance used for logging server events.
    """

    # Ensure each request is handled in a separate daemon thread
    daemon_threads = True
    
    def __init__(self, addr, handler, config):
        """
        Initialize the threaded FTP server.

        Parameters:
            addr (tuple): (host, port) address tuple to bind the server.
            handler (BaseRequestHandler): Handler class for processing requests.
            config (Namespace): Configuration object with server parameters.
        """
        super().__init__(addr, handler)
        self.config = config
        self.lgr = config.lgr
        del config.lgr

def start_server(config):
    """
    Start and run the FTP server using the provided configuration.

    This function binds the server to the given host and port,
    logs startup information, and enters the request-handling loop.

    Parameters:
        config (Namespace): Configuration object containing:
            - bind (str): IP address to bind the server.
            - port (int): Port to listen on.
            - user (str): FTP username.
            - pswd (str): FTP password.
            - directory (str): Directory to serve.
            - lgr (Logger): Preconfigured logger instance.
    """
    with ThreadedThinFTP((config.bind, config.port), ThinFTP, config) as server:
        server.lgr.success(f"Server is now running at {config.bind}:{config.port}")
        server.lgr.debug(f"The Credentials are: [username: {config.user!r}, password: {config.pswd!r}]")
        server.lgr.success(f"The directory served is: {config.directory}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.lgr.info("Gracefully Shutting down Server upon user interrupt")
            server.shutdown()
            server.server_close()
        finally:
            server.lgr.info("Server Shutdown Successfully")
        
