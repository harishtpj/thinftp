# The main FTP handler code for thinFTP
import socketserver
import socket
from .fileman import FileHandler
from .errors import *

class ThinFTP(socketserver.BaseRequestHandler):
    def client_addr(self):
        host, port = self.client_address
        return f"{host}:{port}"
    
    def response(self, sts_code, msg=None, **kwargs):
        resp_map = {
            150: "File status okay; about to open data connection",
            200: "Command {cmd!r} OK",
            220: "Welcome to thinFTP server",
            221: "Goodbye",
            226: "Closing data connection",
            227: "Entering Passive mode ({host},{p1},{p2})",
            230: "User logged in. Proceed",
            257: "{path!r} created",
            331: "Username {user!r} OK. Need Password",
            501: "Syntax Error in parameters or arguments",
            502: "Command {cmd!r} not Implemented",
            503: "Bad sequence of commands: {specific}",
            530: "Authentication Failed",
            550: "No such {obj_kind}: {fname}",
        }
        if msg is None:
            msg = resp_map[sts_code].format(**kwargs)
        resp = f"{sts_code} {msg}.\r\n"
        self.request.sendall(resp.encode())
        return resp
    
    def handle(self):
        self.server.lgr.info(f"Got connection from {self.client_addr()}")
        self.response(220)
        
        self.fileman = FileHandler(self.server.config.directory)
        self.login_user = ''
        self.logged_in = False
        self.data_sock = None
        self.data_conn = None
        
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
                        'PASV': self.ftp_pasv,
                        'LIST': self.ftp_list,
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
                    except TypeError as e:
                        if "missing" in str(e) or "positional" in str(e):
                            self.response(501)
                        else:
                            raise e
            except ClientQuit:
                self.server.lgr.info(f"Connection closed for client {self.client_addr()} upon QUIT")
                    

    def ftp_user(self, uname):
        self.login_user = uname
        self.response(331, user=uname)

    def ftp_pass(self, pswd=''):
        if self.logged_in:
            self.response(202, 'Already logged in')
        elif not self.login_user:
            self.response(503, 'Login with USER first')
        else:
            if (self.login_user == self.server.config.user) and (pswd == self.server.config.pswd):
                self.response(230)
                self.logged_in = True
            else:
                self.login_user = ''
                self.response(530)

    def ftp_pwd(self):
        r = self.response(257, f"{self.fileman.pwd()!r} is the current directory")
        self.server.lgr.debug(f"Replied: {r!r}")

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

    def ftp_pasv(self):
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock.bind((self.server.config.bind, 0))
        self.data_sock.listen(1)

        ip, port = self.data_sock.getsockname()

        p1 = port // 256
        p2 = port % 256
        self.server.lgr.debug(f"Opened PASV Data connection at {ip}:{port}")
        self.response(227, host=ip.replace('.',','), p1=p1, p2=p2)
    
    def ftp_list(self, path='.'):
        if not self.data_sock:
            self.response(503, 'requires PASV first')
        else:
            try:
                lsts = '\r\n'.join(self.fileman.ls(path))
                self.open_data_conn()
                self.response(150)
                self.server.lgr.debug(f"Sending to client {self.client_addr()} via Data conn: \n" + lsts)
                self.data_conn.sendall(lsts.encode())
                self.close_data_conn()
                self.response(226)
            except PermissionError as e:
                self.response(550, msg=e)
                self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")

        
    def ftp_quit(self):
        self.response(221)
        raise ClientQuit

    def open_data_conn(self):
        if self.data_conn:
            self.close_data_conn()
        self.data_conn, addr = self.data_sock.accept()
        self.server.lgr.debug(f"Accepted PASV Data connection from {addr}")
    
    def close_data_conn(self):
        if hasattr(self, 'data_sock'):
            self.data_sock.close()
            self.data_sock = None
        if hasattr(self, 'data_conn'):
            self.data_conn.close()
            self.data_conn = None
        self.server.lgr.debug("Closed PASV Data connection")
      
