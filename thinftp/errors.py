# Custom Error classes for thinFTP

class ClientQuit(Exception):
    pass

class FileHandlerError(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)
