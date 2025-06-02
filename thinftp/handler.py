
"""
The FTP command handler for thinFTP.

This module defines the `ThinFTP` class which handles FTP commands over
a socket connection. It supports standard FTP commands such as USER, PASS,
LIST, RETR, STOR, and PASV mode for data transfers.

Author: M.V. Harish Kumar
"""

import socketserver
import socket
from .fileman import FileHandler
from .errors import *

class ThinFTP(socketserver.BaseRequestHandler):
    """
    The main handler class for the thinFTP server.
    
    This class implements methods for parsing and responding to FTP protocol
    commands from a connected client. It uses a PASV data connection model.

    Attributes:
        fileman (FileHandler): Handles file system operations.
        login_user (str): Currently logging-in or logged-in user.
        logged_in (bool): Authentication state of the client.
        transfer_type (str): Transfer type ('A' for ASCII, 'I' for binary).
        data_sock (socket.socket): Passive mode server socket.
        data_conn (socket.socket): Established data connection with client.
    """

    def client_addr(self):
        """
        Returns the client's address as a string.

        Returns:
            str: The client IP and port in the form 'host:port'.
        """
        host, port = self.client_address
        return f"{host}:{port}"
    
    def response(self, sts_code, msg=None, **kwargs):
        """
        Sends an FTP-compliant response message to the client.

        Args:
            sts_code (int): FTP status code.
            msg (str, optional): Optional custom message.
            **kwargs: Format arguments for message templating.

        Returns:
            str: The full response line sent to the client.
        """
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
        """
        Entry point for handling a single client connection.

        Continuously reads commands, parses them, and dispatches to
        handler methods. Manages login state and handles QUIT properly.
        """
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
        """
        Handle the USER command.

        Args:
            uname (str): Username from the client.

        Returns:
            str: FTP response line.
        """
        self.login_user = uname
        return self.response(331, user=uname)

    def ftp_pass(self, pswd=''):
        """
        Handle the PASS command for user login.

        Args:
            pswd (str): Password from the client.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the PWD command to print current working directory.

        Returns:
            str: FTP response line.
        """
        return self.response(257, f'"{self.fileman.pwd()}" is current directory')

    def ftp_cwd(self, path):
        """
        Handle the CWD command to change directory.

        Args:
            path (str): Path to change to.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the CDUP command to change to parent directory.

        Returns:
            str: FTP response line.
        """
        try:
            self.fileman.cd_up()
            return self.response(250, msg=f"Directory changed to {self.fileman.pwd()}")
        except FileNotFoundError:
            return self.response(550, msg="Failed to change directory. Parent directory does not exist")
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)

    def ftp_mkd(self, path):
        """
        Handle the MKD command to make a new directory.

        Args:
            path (str): Path of directory to create.

        Returns:
            str: FTP response line.
        """
        try:
            self.fileman.mkdir(path)
            return self.response(257, path=self.fileman.get_abs(path))
        except FileExistsError:
            return self.response(550, msg=f"{self.fileman.get_abs(path)}: Directory already exists")

    def ftp_pasv(self):
        """
        Handle the PASV command to initiate passive data connection.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the LIST command to list files and directories.

        Args:
            path (str): Path to list. Defaults to '.'.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the TYPE command to set transfer type.

        Args:
            arg (str): Transfer type (e.g., 'A' or 'I').

        Returns:
            str: FTP response line.
        """
        if arg.upper() in ('A', 'I'):
            self.transfer_type = arg.upper()
            return self.response(200, cmd='TYPE')
        return self.response(504, arg=arg)

    def ftp_retr(self, fname):
        """
        Handle the RETR command to retrieve a file.

        Args:
            fname (str): File to download.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the STOR command to upload a file.

        Args:
            fname (str): File to store.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the SIZE command to get file size.

        Args:
            fname (str): File to check.

        Returns:
            str: FTP response line.
        """
        try:
            size = self.fileman.size(fname)
            return self.response(213, msg=size)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
        except FileHandlerError as e:
            return self.response(550, msg=e)

    def ftp_dele(self, fname):
        """
        Handle the DELE command to delete a file.

        Args:
            fname (str): File to delete.

        Returns:
            str: FTP response line.
        """
        try:
            self.fileman.delete(fname)
            return self.response(250, "File deleted")
        except FileNotFoundError:
            return self.response(550, obj_kind="File", fname=fname)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
    def ftp_rmd(self, path):
        """
        Handle the RMD command to remove a directory.

        Args:
            path (str): Directory to remove.

        Returns:
            str: FTP response line.
        """
        try:
            self.fileman.rmdir(path)
            return self.response(250, "Directory deleted")
        except FileNotFoundError:
            return self.response(550, obj_kind="Directory", fname=path)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
    def ftp_rnfr(self, old):
        """
        Handle the RNFR command (rename from).

        Args:
            old (str): Existing file/directory name.

        Returns:
            str: FTP response line.
        """
        try:
            self.fileman.rename_from(old)
            return self.response(350, cmd='RNTO')
        except FileNotFoundError:
            return self.response(550, obj_kind="File", fname=old)
        except PermissionError as e:
            self.server.lgr.error(f"Attempt by client {self.client_addr()} to violate server: {e}")
            return self.response(550, msg=e)
    
    def ftp_rnto(self, new):
        """
        Handle the RNTO command (rename to).

        Args:
            new (str): New file/directory name.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the FEAT command to list supported features.

        Returns:
            str: FTP response line.
        """
        features = ('PASV', 'SIZE', 'UTF8')
        self.response(211, custom='Features')
        for feat in features:
            self.request.sendall(f" {feat}\r\n".encode())
        return self.response(211, msg="End")
    
    def ftp_help(self, *args):
        """
        Handle the HELP command.

        Args:
            *args: Optional command to get help for.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the NLST command to list names only.

        Args:
            path (str): Path to list. Defaults to '.'.

        Returns:
            str: FTP response line.
        """
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
        """
        Handle the QUIT command to end the session.

        Returns:
            None

        Raises:
            ClientQuit: Raised to break from the main loop.
        """
        self.response(221)
        raise ClientQuit

    def open_data_conn(self):
        """
        Accepts the incoming data connection from the client.
        """
        if self.data_conn:
            self.close_data_conn()
        self.data_conn, addr = self.data_sock.accept()
        self.server.lgr.debug(f"Accepted PASV Data connection from {addr}")
    
    def close_data_conn(self):
        """
        Closes the current data connection and socket.
        """
        if hasattr(self, 'data_sock'):
            self.data_sock.close()
            self.data_sock = None
        if hasattr(self, 'data_conn'):
            self.data_conn.close()
            self.data_conn = None
        self.server.lgr.debug("Closed PASV Data connection")
      
