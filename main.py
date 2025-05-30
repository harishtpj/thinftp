# The main CLI entrypoint for thinFTP Server
import argparse
import getpass
from thinftp.logger import get_logger
from thinftp.server import start_server

parser = argparse.ArgumentParser(prog="thinftp")

parser.add_argument('-v', '--version',
                    action="version",
                    version="%(prog)s v0.1.0")

parser.add_argument('-b', '--bind',
                    default="0.0.0.0",
                    help="Binds the IP address of the server (default: %(default)s)")

parser.add_argument('-p', '--port',
                    default=2528,
                    type=int,
                    help="Sets the Port of the server (default: %(default)s)")

parser.add_argument('-u', '--user',
                    default=getpass.getuser(),
                    help="Sets the Username for the server")

parser.add_argument('-d', '--directory',
                    default=".",
                    help="Sets the root Directory (default: %(default)s)")

parser.add_argument('-D', '--debug',
                    action='store_true',
                    help="Enable DEBUG logs")

opts = parser.parse_args()

opts.pswd = getpass.getpass(f"Set Password for {opts.user}: ")
opts.lgr = get_logger(debug=opts.debug)
opts.lgr.info("Welcome to thinFTP server")
start_server(opts)

