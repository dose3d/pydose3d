class WrongDicomFormatException(Exception):
    """Exception raises when a given DICOM file 
    is not ct dicom, but rt. """
    pass

class NotADicomFileException(Exception):
    """Exception raises when a given file
    is not a dicom file. """
    pass

class NotEqualMasksSizes(Exception):
    """Exception raises when the two
    masks have different dimensions. """
    pass

class RequestedSlicesIndexOutofRange(Exception):
    """Exception raises when given 
    slices have indexes indexes out of range.

    Attributes:
        dicom3dimage -- 3d dicom image to operate on
        index -- given index
    """
    def __init__(self, dicom3dimage, index):
        self.dicom3dimage = dicom3dimage
        self.index = index
        self.message = f"{index} is out of range for image with {dicom3dimage.shape[2]} spatial size."
        super().__init__(self.message)

class IndexesHaveNotCorrectType(Exception):
    """Exception raises given indexes are not int. """
    pass

