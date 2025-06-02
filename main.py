# The main CLI entrypoint for thinFTP Server
#
# This script parses command-line arguments and starts the thinFTP server.

import argparse
import getpass
import sys
import traceback

from thinftp.logger import get_logger
from thinftp.server import start_server

# Parse command-line arguments
parser = argparse.ArgumentParser(prog="thinftp",
                                 description="A simple FTP server for testing purposes",
                                 epilog="Examples:\n"
                                        "  thinftp -h localhost -p 2121 -u testuser -d ./testdir\n"
                                        "  thinftp --bind localhost --port 2121 --user testuser --directory ./testdir")

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

# Get the password from the user
opts.pswd = getpass.getpass(f"Set Password for {opts.user}: ")

# Get the logger instance
opts.lgr = get_logger(debug=opts.debug)

# Log the startup message
opts.lgr.info("Welcome to thinFTP server")

try:
    # Start the server
    start_server(opts)
except Exception as e:
    # Handle any unhandled exceptions
    if opts.debug:
        # Reraise the exception if --debug is specified
        raise
    else:
        # Log the exception if --debug is not specified
        tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        opts.lgr.critical("Unhandled exception: \n"+ tb)
        # Exit with a non-zero status code
        sys.exit(1)

