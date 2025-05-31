# The main FTP handler code for thinFTP
import socketserver
from .errors import *

class ThinFTP(socketserver.BaseRequestHandler):
    def response(self, sts_code, msg=None, **kwargs):
        resp_map = {
            220: "Welcome to thinFTP server",
            221: "Goodbye",
            230: "User logged in. Proceed",
            331: "Username {user!r} OK. Need Password",
            501: "Syntax Error in parameters or arguments",
            502: "Command {cmd!r} not Implemented",
            530: "Authentication Failed",
            
        }
        if msg is None:
            msg = resp_map[sts_code].format(**kwargs)
        self.request.sendall(f"{sts_code} {msg}.\r\n".encode())
    
    def handle(self):
        self.server.lgr.info(f"Got connection from {self.client_address}")
        self.response(220)
        
        # self.fileman = 
        self.login_user = ''
        self.logged_in = False
        
        with self.request.makefile("rwb") as conn:
            try:
                while True:
                    line = conn.readline()
                    if not line:
                        self.server.lgr.error(f"Connection closed unexpectedly by client: {self.client_address}.")
                        break

                    cmd = line.decode().strip()
                    if not cmd:
                        continue
                
                    self.server.lgr.debug(f"Received command: [{cmd}] from client {self.client_address}")
                    verb, _, args = cmd.partition(' ')

                    verb_map = {
                        'USER': self.ftp_user,
                        'PASS': self.ftp_pass,
                        'QUIT': self.ftp_quit,
                    }
                    before_login = ('USER', 'PASS', 'QUIT')

                    try:
                        verb = verb.upper()
                        args = args.split()
                        if (not self.logged_in) and (verb not in before_login):
                            self.response(530, 'Access Denied')
                            continue
                        verb_map[verb](*args)
                    except KeyError:
                        self.response(502, cmd=verb)
                    except TypeError:
                        self.response(501)                    
            except ClientQuit:
                self.server.lgr.info(f"Connection closed for client {self.client_address} upon QUIT")
                    

    def ftp_user(self, uname):
        self.login_user = uname
        self.response(331, user=uname)

    def ftp_pass(self, pswd):
        if not self.login_user:
            self.response(503, 'Login with USER first')
        else:
            if (self.login_user == self.server.config.user) and (pswd == self.server.config.pswd):
                self.response(230)
                self.logged_in = True
            else:
                self.login_user = ''
                self.response(530)

    def ftp_quit(self):
        self.response(221)
        raise ClientQuit
        


        
