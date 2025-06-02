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
            200: "Command {cmd} OK",
            211: "-{custom}", # Custom ones are specified below
            214: "-{custom}", # Custom ones are specified below
            220: "Welcome to thinFTP server",
            221: "Goodbye",
            226: "Closing data connection",
            227: "Entering Passive mode ({host},{p1},{p2})",
            230: "User logged in. Proceed",
            257: '"{path}" created', # Custom ones are specified below
            331: "Username {user!r} OK. Need Password",
            350: "Ready for {cmd}",
            501: "Syntax Error in parameters or arguments",
            502: "Command {cmd!r} not Implemented",
            503: "Requires {cmd} first",
            504: "Command TYPE not implemented for the parameter {arg}",
            530: "Authentication Failed",
            550: "No such {obj_kind}: {fname}", # Custom ones are specified below
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
        self.transfer_type = 'I'
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

                    self.verb_map = {
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
                        'OPTS': lambda kind, switch: self.response(200, cmd=verb),
                        'TYPE': self.ftp_type,
                        'RETR': self.ftp_retr,
                        'SIZE': self.ftp_size,
                        'DELE': self.ftp_dele,
                        'RMD': self.ftp_rmd,
                        'RNFR': self.ftp_rnfr,
                        'RNTO': self.ftp_rnto,
                        'STOR': self.ftp_stor,
                        'SYST': lambda: self.response(215, 'UNIX Type: L8'),
                        'FEAT': self.ftp_feat,
                        'HELP': self.ftp_help,
                        'NLST': self.ftp_nlst,
                    }
                    before_login = ('USER', 'PASS', 'QUIT')
                    single_arg_verbs = ('RETR', 'STOR')

                    try:
                        verb = verb.upper()
                        if (not self.logged_in) and (verb not in before_login):
                            self.response(530, 'Access Denied')
                            continue
                        
                        fn = self.verb_map.get(verb)
                        if not fn:
                            resp = self.response(502, cmd=verb)
                        else:
                            resp = fn(args) if verb in single_arg_verbs else fn(*args.split())
                            
                        self.server.lgr.debug(f"Replied {self.client_addr()}: {resp!r}")
                    except TypeError as e:
                        if "missing" in str(e) or "positional" in str(e):
                            self.response(501)
                        else:
                            raise e
            except ClientQuit:
                self.server.lgr.info(f"Connection closed for client {self.client_addr()} upon QUIT")
                    

    def ftp_user(self, uname):
        self.login_user = uname
        return self.response(331, user=uname)

    def ftp_pass(self, pswd=''):
        if self.logged_in:
            return self.response(202, 'Already logged in')
        elif not self.login_user:
            return self.response(503, 'Login with USER first')
        else:
            if (self.login_user == self.server.config.user) and (pswd == self.server.config.pswd):
                self.logged_in = True
                return self.response(230)
            else:
                self.login_user = ''
                return self.response(530)

    def ftp_pwd(self):
        return self.response(257, f'"{self.fileman.pwd()}" is current directory')

    def ftp_cwd(self, path):
        try:
            self.fileman.cwd(path)
            return self.response(250, msg=f"Directory changed to {self.fileman.pwd()}")
        except FileNotFoundError:
            return self.response(550, obj_kind="Directory", fname=path)
        except NotADirectoryError:
            return self.response(550, msg=f"The directory name is invalid: {path!r}")
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)

    def ftp_cdup(self):
        try:
            self.fileman.cd_up()
            return self.response(250, msg=f"Directory changed to {self.fileman.pwd()}")
        except FileNotFoundError:
            return self.response(550, msg="Failed to change directory. Parent directory does not exist")
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)

    def ftp_mkd(self, path):
        try:
            self.fileman.mkdir(path)
            return self.response(257, path=self.fileman.get_abs(path))
        except FileExistsError:
            return self.response(550, msg=f"{self.fileman.get_abs(path)}: Directory already exists")

    def ftp_pasv(self):
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock.bind((self.server.config.bind, 0))
        self.data_sock.listen(1)

        ip, _ = self.request.getsockname()
        _, port = self.data_sock.getsockname()

        p1 = port // 256
        p2 = port % 256
        self.server.lgr.debug(f"Opened PASV Data connection at {ip}:{port}")
        return self.response(227, host=ip.replace('.',','), p1=p1, p2=p2)
    
    def ftp_list(self, path='.'):
        if not self.data_sock:
            return self.response(503, cmd='PASV')
        try:
            lsts = '\r\n'.join(self.fileman.ls(path))
            self.open_data_conn()
            self.response(150)
            self.server.lgr.debug(f"Sending to client {self.client_addr()} via Data conn: \n" + lsts)
            self.data_conn.sendall(lsts.encode())
            self.close_data_conn()
            return self.response(226)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)

    def ftp_type(self, arg):
        if arg.upper() in ('A', 'I'):
            self.transfer_type = arg.upper()
            return self.response(200, cmd='TYPE')
        return self.response(504, arg=arg)

    def ftp_retr(self, fname):
        if not self.data_sock:
            return self.response(503, cmd='PASV')
        try:
            self.open_data_conn()
            self.response(150)
            self.server.lgr.debug(f"Sending to client {self.client_addr()} via Data conn:")
            for chunk in self.fileman.read(fname, self.transfer_type):
                self.data_conn.sendall(chunk)
            try:
                self.server.lgr.debug("The file ends as follows: \n" + chunk.decode())
            except UnboundLocalError:
                pass
            self.close_data_conn()
            return self.response(226)
        except FileNotFoundError:
            return self.response(550, obj_kind="File", fname=fname)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
    def ftp_stor(self, fname):
        if not self.data_sock:
            return self.response(503, cmd='PASV')
        try:
            self.open_data_conn()
            self.response(150)
            self.server.lgr.debug(f"Receiving from client {self.client_addr()} via Data conn:")
            
            def data_recv():
                while True:
                    chunk = self.data_conn.recv(8192)
                    if not chunk:
                        break
                    yield chunk
            self.fileman.write(fname, data_recv())
            self.close_data_conn()
            return self.response(226)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)

    def ftp_size(self, fname):
        try:
            size = self.fileman.size(fname)
            return self.response(213, msg=size)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
        except FileHandlerError as e:
            return self.response(550, msg=e)

    def ftp_dele(self, fname):
        try:
            self.fileman.delete(fname)
            return self.response(250, "File deleted")
        except FileNotFoundError:
            return self.response(550, obj_kind="File", fname=fname)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
    def ftp_rmd(self, path):
        try:
            self.fileman.rmdir(path)
            return self.response(250, "Directory deleted")
        except FileNotFoundError:
            return self.response(550, obj_kind="Directory", fname=path)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
    def ftp_rnfr(self, old):
        try:
            self.fileman.rename_from(old)
            return self.response(350, cmd='RNTO')
        except FileNotFoundError:
            return self.response(550, obj_kind="File", fname=old)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
    def ftp_rnto(self, new):
        if not hasattr(self.fileman, 'ren_old') or not self.fileman.ren_old:
            return self.response(503, cmd='RNFR')
        try:
            self.fileman.rename_to(new)
            return self.response(250, "File renamed")
        except FileNotFoundError:
            return self.response(550, obj_kind="File", fname=new)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
    def ftp_feat(self):
        features = ('PASV', 'SIZE', 'UTF8')
        self.response(211, custom='Features')
        for feat in features:
            self.request.sendall(f" {feat}\r\n".encode())
        self.response(211, msg="End")
    
    def ftp_help(self, *args):
        if args:
            cmd = args[0].upper()
            return self.response(214, f"No Detailed help available for {cmd}")
        cmds = sorted(self.verb_map.keys())
        cmd_ln = [cmds[i:i+8] for i in range(0, len(cmds), 8)]
        self.response(214, custom='The following commands are implemented')
        for ln in cmd_ln:
            self.request.sendall(f" {' '.join(ln)}\r\n".encode())
        return self.response(214, "Help OK")

    def ftp_nlst(self, path='.'):
        if not self.data_sock:
            return self.response(503, cmd='PASV')
        try:
            lsts = '\r\n'.join([x.name for x in self.fileman.name_ls(path)])
            self.open_data_conn()
            self.response(150)
            self.server.lgr.debug(f"Sending to client {self.client_addr()} via Data conn: \n" + lsts)
            self.data_conn.sendall(lsts.encode())
            self.close_data_conn()
            return self.response(226)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
                         
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
      
