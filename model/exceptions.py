# New Exceptions for the application
class InvalidClassifiedImageException(Exception):
    """
    The classified image is incorrect. Not all values on the image could be divided by 100.

    """

    def __init__(self, input_path: str):
        message = (
            "Not all values can be divided by 100 on the image! The image: "
            + input_path
        )
        super(InvalidClassifiedImageException, self).__init__(message)


class TooLargeImageException(Exception):
    """
    The image to be opened exceeds the maximum supported pixel count.

    """

    def __init__(self, actual_count: float, max_count: float, input_path: str):
        message = (
            str(actual_count)
            + " pixels -> Too large image! The limit is "
            + str(max_count)
            + " pixels. The image: "
            + input_path
        )
        super(TooLargeImageException, self).__init__(message)


class CodValueNotPresentException(Exception):
    """
    The classified image does not contain the specified class.

    """

    def __init__(self, cod_type: str, cod_value: int, input_path: str):
        message = (
            cod_type.upper()
            + "_COD value ("
            + str(cod_value)
            + ") is not on the image! Wrong "
            + cod_type.upper()
            + " Class ID! The image: "
            + input_path
        )
        super(CodValueNotPresentException, self).__init__(message)


class NotEnoughBandsException(Exception):
    """
    The image to be opened does not have enough bands.

    """

    def __init__(self, available_bands: int, needed_bands: int, input_path: str):
        message = (
            "Available bands: "
            + str(available_bands)
            + " -> "
            + str(needed_bands)
            + " bands needed! The image: "
            + input_path
        )
        super(NotEnoughBandsException, self).__init__(message)


class CanvasNameException(Exception):
    """
    The referenced Canvas does not exist.

    """

    def __init__(self, canvas_name: str):
        message = canvas_name + " -> Wrong canvas name!"
        super(CanvasNameException, self).__init__(message)


class ImageTypeException(Exception):
    """
    Wrong image type given to Canvas.

    """

    def __init__(self, image_type: str):
        message = image_type + " -> Wrong image type!"
        super(ImageTypeException, self).__init__(message)


class PictureDoesNotExistException(Exception):
    """
    The image to be opened does not exist.

    """

    def __init__(self, image_path: str):
        message = "The image you want to open does not exist! The image: " + image_path
        super(PictureDoesNotExistException, self).__init__(message)


class RandomForestFileException(Exception):
    """
    Incorrect Random Forest (.sav) file.

    """

    def __init__(self, rf_type: str):
        message = rf_type + " detection -> Wrong Random Forest file!"
        super(RandomForestFileException, self).__init__(message)


class HotspotRandomForestFileException(RandomForestFileException):
    """
    Incorrect Random Forest (.sav) file for Hot-spot detection process.

    """

    def __init__(self):
        super(HotspotRandomForestFileException, self).__init__("Hot-spot")


class FloatingRandomForestFileException(RandomForestFileException):
    """
    Incorrect Random Forest (.sav) file for Floating waste detection process.

    """

    def __init__(self):
        super(FloatingRandomForestFileException, self).__init__("Floating waste")


class FileExtensionException(Exception):
    """
    Incorrect file extension.

    """

    def __init__(
        self, wanted_file_extension: str, got_file_extension: str, input_path: str
    ):
        message = (
            got_file_extension
            + " -> File extension must be "
            + wanted_file_extension
            + ". The file: "
            + input_path
        )
        super(FileExtensionException, self).__init__(message)


class JsonFileExtensionException(FileExtensionException):
    """
    Incorrect file extension. JSON file expected.

    """

    def __init__(self, got_file_extension: str, input_path: str):
        super(JsonFileExtensionException, self).__init__(
            ".json", got_file_extension, input_path
        )


class PersistenceLoadException(Exception):
    """
    The saved settings could not be opened. The config file is corrupted.

    """

    def __init__(self):
        message = "Could not load saved settings. Invalid configuration!"
        super(PersistenceLoadException, self).__init__(message)
