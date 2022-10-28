import copy
import pyproj

from typing import Dict, Tuple, List
from abc import ABC, abstractmethod


class BaseAPI(ABC):
    """
    Base class for API classes.

    """

    def __init__(self, config_file: Dict, data_file: Dict) -> None:
        """
        Constructor of BaseApi class.

        :param config_file: dictionary containing the settings parameters
        :param data_file: dictionary containing the AOIs in GeoJSON format
        :return: None
        """

        self.config_file = config_file
        self.data_file = BaseAPI.convert_multipolygons_to_polygons(data_file)
        self.data_file = BaseAPI.transform_coordinates_to_wgs84(self.data_file)

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

        :param time_interval: acquisition time interval of images
        :param max_result_limit: maximum number of results
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

    @staticmethod
    def convert_multipolygons_to_polygons(data_file: Dict) -> Dict:
        """
        Converts MultiPolygon shapes to Polygons.

        :param data_file: dictionary containing the AOIs in GeoJSON format
        :return: converted version of data_file
        """

        new_data_file = copy.deepcopy(data_file)

        for feature in new_data_file["features"]:
            if feature["geometry"]["type"] == "MultiPolygon":
                feature["geometry"]["type"] = "Polygon"
                feature["geometry"]["coordinates"] = feature["geometry"]["coordinates"][0]

        return new_data_file

    @staticmethod
    def transform_coordinates(coords: List[List[int]], input_crs: str, output_crs: str) -> List[List[int]]:
        """
        Transforms coordinates from one CRS to another.

        :param coords: list of coordinates: [[x1, y1], [x2, y2], ...]
        :param input_crs: original CRS of coordinates
        :param output_crs: wanted CRS of coordinates
        :return: list of transformed coordinates
        """

        transformed_coords = copy.deepcopy(coords)

        transformer = pyproj.Transformer.from_crs(crs_from=input_crs, crs_to=output_crs, always_xy=True)

        for i in range(len(coords)):
            x, y = coords[i]
            new_x, new_y = transformer.transform(x, y)
            transformed_coords[i][0] = new_x
            transformed_coords[i][1] = new_y

        return transformed_coords

    @staticmethod
    def transform_coordinates_to_wgs84(data_file: Dict) -> Dict:
        """
        Transforms all coordinates from given CRS to WGS84.

        :param data_file: dictionary containing the AOIs in GeoJSON format
        :return: transformed version of data_file
        """

        if "crs" in data_file.keys() and data_file["crs"]["properties"]["name"] != "urn:ogc:def:crs:OGC:1.3:CRS84":
            transformed_data_file = copy.deepcopy(data_file)
            for feature in transformed_data_file["features"]:

                input_crs = transformed_data_file["crs"]["properties"]["name"]
                output_crs = "epsg:4326"

                coordinates = feature["geometry"]["coordinates"][0]

                transformed_coords = BaseAPI.transform_coordinates(coordinates, input_crs, output_crs)

                feature["geometry"]["coordinates"] = [transformed_coords]

            transformed_data_file["crs"]["properties"]["name"] = "urn:ogc:def:crs:OGC:1.3:CRS84"

            return transformed_data_file
        else:
            return data_file
