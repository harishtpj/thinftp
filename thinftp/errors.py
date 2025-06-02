"""
Custom exception classes for the thinFTP server.

These exceptions are used to signal specific error conditions
during FTP command handling and file operations.

Author: M.V. Harish Kumar
"""

class ClientQuit(Exception):
    """
    Exception raised to indicate that the client has requested to quit.

    This is used internally to break the connection handling loop
    after receiving the FTP `QUIT` command.
    """
    pass

class FileHandlerError(Exception):
    """
    Exception raised for errors occurring in file operations.

    Attributes:
        message (str): Description of the file handling error.
    """

    def __init__(self, msg):
        """
        Initialize the FileHandlerError.

        Args:
            msg (str): The error message describing what went wrong.
        """
        self.message = msg
        super().__init__(self.message)
