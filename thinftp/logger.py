
"""
Custom logger setup for the thinFTP server.

This module defines a custom logging level called "SUCCESS", provides
colored log formatting for different levels, and supplies a helper
function `get_logger` to configure a logger instance for use
throughout the application.
"""

import logging as l

SUCCESS = 25
l.addLevelName(SUCCESS, 'SUCCESS')

def success(self, message, *args, **kwargs):
    """
    Log a message with the custom SUCCESS level.

    Parameters:
        message (str): The message to be logged.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, message, args, **kwargs)


# Add the custom success method to the Logger class
l.Logger.success = success

class Formatter(l.Formatter):
    """
    Custom log formatter with ANSI color codes for console output.

    Formats log messages with different colors depending on the level,
    improving readability during development or monitoring.
    """

    red = '\033[31m'
    bold_red = '\033[1;31m'
    yellow = '\033[93m'
    green = '\033[32m'
    gray = '\033[38;20m'
    bold = '\033[1m'
    reset = '\033[0m'
    format = '[%(asctime)s] [%(levelname)-8s] %(message)s'

    # Mapping log levels to colorized formats
    FORMATS = {
        l.DEBUG: gray + format + reset,
        l.INFO: bold + format + reset,
        SUCCESS: green + format + reset,
        l.WARNING: yellow + format + reset,
        l.ERROR: red + format + reset,
        l.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        """
        Apply the appropriate color format to the log record.

        Parameters:
            record (LogRecord): The log record to format.

        Returns:
            str: The formatted log message string.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = l.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name="thinFTP", debug=False):
    """
    Create and configure a logger with color output and custom SUCCESS level.

    Parameters:
        name (str): Name of the logger. Defaults to "thinFTP".
        debug (bool): If True, sets the log level to DEBUG; otherwise INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = l.getLogger(name)
    logger.setLevel(l.DEBUG if debug else l.INFO)

    # Prevent duplicate handlers
    if not logger.hasHandlers():
        handler = l.StreamHandler()
        handler.setFormatter(Formatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger
