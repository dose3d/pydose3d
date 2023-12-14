class Pydose3dException(Exception):
    """Global exception class for PyDose3d"""
    def __init__(self, message):
        self.error_txt = "Empty file list: " + message
        super().__init__(self.error_txt)

class Pydose3dEmptyFileList(Pydose3dException):
    """Exception raises when a file list is empty """
    def __init__(self, message):
        self.error_txt = "Empty file list: " + message
        super().__init__(self.error_txt)

class Pydose3dFileNotFoundException(Pydose3dException):
    """Exception raises when a file list is empty """
    def __init__(self, message):
        self.error_txt = "File not found: " + message
        super().__init__(self.error_txt)

class Pydose3dFileNoSuchLayerException(Pydose3dException):
    """Exception raises when a file list is empty """
    def __init__(self, message):
        self.error_txt = f"Requested layer {message} doesn't exist in avalilable layer pads data"
        super().__init__(self.error_txt)

