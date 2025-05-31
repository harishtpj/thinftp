# Code for thinFTP Server
import socketserver
from .handler import ThinFTP
from .logger import get_logger

class ThreadedThinFTP(socketserver.ThreadingTCPServer):
    daemon_threads = True
    
    def __init__(self, addr, handler, config):
        super().__init__(addr, handler)
        self.config = config
        self.lgr = config.lgr
        del config.lgr

def start_server(config):
    with ThreadedThinFTP((config.bind, config.port), ThinFTP, config) as server:
        server.lgr.success(f"Server is now running at {config.bind}:{config.port}")
        server.lgr.debug(f"The Credentials are: [username: {config.user}, password: {config.pswd}]")
        server.lgr.success(f"The directory served is: {config.directory}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.lgr.info("Gracefully Shutting down Server upon user interrupt")
            server.shutdown()
            server.server_close()
        finally:
            server.lgr.info("Server Shutdown Successfully")
        
