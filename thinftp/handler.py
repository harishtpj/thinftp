# The main FTP handler code for thinFTP
import socketserver
from .fileman import FileHandler
from .errors import *

class ThinFTP(socketserver.BaseRequestHandler):
    def client_addr(self):
        host, port = self.client_address
        return f"{host}:{port}"
    
    def response(self, sts_code, msg=None, **kwargs):
        resp_map = {
            200: "Command {cmd!r} OK",
            220: "Welcome to thinFTP server",
            221: "Goodbye",
            230: "User logged in. Proceed",
            257: "{path!r} created",
            331: "Username {user!r} OK. Need Password",
            501: "Syntax Error in parameters or arguments",
            502: "Command {cmd!r} not Implemented",
            530: "Authentication Failed",
            550: "No such {obj_kind}: {fname}",
        }
        if msg is None:
            msg = resp_map[sts_code].format(**kwargs)
        self.request.sendall(f"{sts_code} {msg}.\r\n".encode())
    
    def handle(self):
        self.server.lgr.info(f"Got connection from {self.client_addr()}")
        self.response(220)
        
        self.fileman = FileHandler(self.server.config.directory)
        self.login_user = ''
        self.logged_in = False
        
        with self.request.makefile("rwb") as conn:
            try:
                while True:
                    line = conn.readline()
                    if not line:
                        self.server.lgr.error(f"Connection closed unexpectedly by client: {self.client_addr()}.")
                        break

                    cmd = line.decode().strip()
                    if not cmd:
                        continue
                
                    self.server.lgr.debug(f"Received command: [{cmd}] from client {self.client_addr()}")
                    verb, _, args = cmd.partition(' ')

                    verb_map = {
                        'USER': self.ftp_user,
                        'PASS': self.ftp_pass,
                        'QUIT': self.ftp_quit,
                        'NOOP': lambda: self.response(200, cmd=verb),
                        'PWD': self.ftp_pwd,
                        'CWD': self.ftp_cwd,
                        'CDUP': self.ftp_cdup,
                        'MKD': self.ftp_mkd,
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
                self.server.lgr.info(f"Connection closed for client {self.client_addr()} upon QUIT")
                    

    def ftp_user(self, uname):
        self.login_user = uname
        self.response(331, user=uname)

    def ftp_pass(self, pswd=''):
        if not self.login_user:
            self.response(503, 'Login with USER first')
        else:
            if (self.login_user == self.server.config.user) and (pswd == self.server.config.pswd):
                self.response(230)
                self.logged_in = True
            else:
                self.login_user = ''
                self.response(530)

    def ftp_pwd(self):
        self.response(257, f"{self.fileman.pwd()!r} is the current directory")

    def ftp_cwd(self, path):
        try:
            self.fileman.cwd(path)
            self.response(250, msg=f"Directory changed to {self.fileman.pwd()!r}")
        except FileNotFoundError:
            self.response(550, obj_kind="Directory", fname=path)
        except NotADirectoryError:
            self.response(550, msg=f"The directory name is invalid: {path!r}")
        except PermissionError as e:
            self.response(550, msg=e)
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")

    def ftp_cdup(self):
        try:
            self.fileman.cd_up()
            self.response(250, msg=f"Directory changed to {self.fileman.pwd()}")
        except FileNotFoundError:
            self.response(550, msg="Failed to change directory. Parent directory does not exist")
        except PermissionError as e:
            self.response(550, msg=e)
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")

    def ftp_mkd(self, path):
        try:
            self.fileman.mkdir(path)
            self.response(257, path=self.fileman.get_abs(path))
        except FileExistsError:
            self.response(550, msg=f"{self.fileman.get_abs(path)}: Directory already exists")
        
    def ftp_quit(self):
        self.response(221)
        raise ClientQuit
      
