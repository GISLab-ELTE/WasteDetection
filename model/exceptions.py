# New Exceptions for the application
class TooLargeImageException(Exception):
    """
    The image to be opened exceeds the maximum supported pixel count.

    """

    def __init__(self, actual_count: float, max_count: float, input_path: str):
        message = (
            f"{str(actual_count)} pixels -> Too large image! The limit is {str(max_count)} pixels. "
            f"The image: {input_path}"
        )
        super(TooLargeImageException, self).__init__(message)


class NotEnoughBandsException(Exception):
    """
    The image to be opened does not have enough bands.

    """

    def __init__(self, available_bands: int, needed_bands: int, input_path: str):
        message = (
            f"Available bands: {str(available_bands)} -> {str(needed_bands)} bands needed! " f"The image: {input_path}"
        )
        super(NotEnoughBandsException, self).__init__(message)


class CanvasNameException(Exception):
    """
    The referenced Canvas does not exist.

    """

    def __init__(self, canvas_name: str):
        message = f"{canvas_name} -> Wrong canvas name!"
        super(CanvasNameException, self).__init__(message)


class ImageTypeException(Exception):
    """
    Wrong image type given to Canvas.

    """

    def __init__(self, image_type: str):
        message = f"{image_type} -> Wrong image type!"
        super(ImageTypeException, self).__init__(message)


class PictureDoesNotExistException(Exception):
    """
    The image to be opened does not exist.

    """

    def __init__(self, image_path: str):
        message = f"The image you want to open does not exist! The image: {image_path}"
        super(PictureDoesNotExistException, self).__init__(message)


class UNETFileException(Exception):
    """
    Incorrect UNET (.sav) file.

    """

    def __init__(self, unet_model: str):
        message = f"{unet_model} architecture -> Wrong UNET file"
        super(UNETFileException, self).__init__(message)


class RandomForestFileException(Exception):
    """
    Incorrect Random Forest (.sav) file.

    """

    def __init__(self, rf_type: str):
        message = f"{rf_type} detection -> Wrong Random Forest file!"
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

    def __init__(self, wanted_file_extension: str, got_file_extension: str, input_path: str):
        message = f"{got_file_extension} -> File extension must be {wanted_file_extension}. The file: {input_path}"
        super(FileExtensionException, self).__init__(message)


class JsonFileExtensionException(FileExtensionException):
    """
    Incorrect file extension. JSON file expected.

    """

    def __init__(self, got_file_extension: str, input_path: str):
        super(JsonFileExtensionException, self).__init__(".json", got_file_extension, input_path)


class PersistenceLoadException(Exception):
    """
    The saved settings could not be opened. The config file is corrupted.

    """

    def __init__(self):
        message = "Could not load saved settings. Invalid configuration!"
        super(PersistenceLoadException, self).__init__(message)
