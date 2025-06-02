"""thinFTP - A minimal, lightweight FTP server implementation in Python."""

__version__ = "0.1.1"
__author__ = "M.V. Harish Kumar"
__email__ = "harishtpj@outlook.com"

# Import main classes for easy access
try:
    from .server import ThreadedThinFTP
    from .handler import ThinFTP
    from .logger import setup_logger
    
    __all__ = [
        "ThreadedThinFTP",
        "ThinFTP", 
        "setup_logger",
        "__version__"
    ]
except ImportError:
    # Handle import errors gracefully during documentation build
    __all__ = ["__version__"]
