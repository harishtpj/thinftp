# Custom Logger for thinFTP
import logging as l

SUCCESS = 25
l.addLevelName(SUCCESS, 'SUCCESS')

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, message, args, **kwargs)

l.Logger.success = success

class Formatter(l.Formatter):
    red = '\033[31m'
    bold_red = '\033[1;31m'
    yellow = '\033[93m'
    green = '\033[32m'
    gray = '\033[38;20m'
    bold = '\033[1m'
    reset = '\033[0m'
    format = '[%(asctime)s] [%(levelname)-8s] %(message)s'

    FORMATS = {
        l.DEBUG: gray + format + reset,
        l.INFO: bold + format + reset,
        SUCCESS: green + format + reset,
        l.WARNING: yellow + format + reset,
        l.ERROR: red + format + reset,
        l.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = l.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name="thinFTP", debug=False):
    logger = l.getLogger(name)
    logger.setLevel(l.DEBUG if debug else l.INFO)

    if not logger.hasHandlers():
        handler = l.StreamHandler()
        handler.setFormatter(Formatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger
