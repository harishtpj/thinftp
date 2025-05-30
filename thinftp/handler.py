# The main FTP handler code for thinFTP
import socketserver

class ThinFTP(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.sendall(b"220 Welcome to thinFTP server\r\n")
        # self.fileman = 

        self.server.lgr.info(f"Got connection from {self.client_address}")


        
