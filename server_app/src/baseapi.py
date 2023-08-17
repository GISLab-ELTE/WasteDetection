from typing import Dict, Tuple
from abc import ABC, abstractmethod


class BaseAPI(ABC):
    """
    Base class for API classes.

    """

    def __init__(self, config_file: Dict, data_file: Dict) -> None:
        """
        Constructor of BaseApi class.

        :param config_file: Dictionary containing the settings parameters.
        :param data_file: Dictionary containing the AOIs in GeoJSON format.
        :return: None
        """

        self.config_file = config_file
        self.data_file = data_file

    @abstractmethod
    def login(self) -> None:
        """
        Logs into the API account.

        :return: None
        """

        pass

    @abstractmethod
    def search(self, time_interval: Tuple[str, str], max_result_limit: int) -> None:
        """
        Searches the available images.

        :param time_interval: Acquisition time interval of images.
        :param max_result_limit: Maximum number of results.
        :return: None
        """

        pass

    @abstractmethod
    def order(self) -> None:
        """
        Places the orders so that the unavailable images become available.

        :return: None
        """

        pass

    @abstractmethod
    def download(self) -> None:
        """
        Downloads the available images.

        :return: None
        """

        pass