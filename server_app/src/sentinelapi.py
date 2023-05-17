import datetime as dt

from baseapi import BaseAPI
from typing import Dict, Tuple, List

from sentinelhub import (
    SHConfig,
    CRS,
    BBox,
    DataCollection,
    SentinelHubCatalog,
    MimeType,
    SentinelHubRequest,
    bbox_to_dimensions,
    filter_times
)


class SentinelAPI(BaseAPI):
    """
    API class for downloading Sentinel-2 satellite images.

    """

    def __init__(self, config_file: Dict, data_file: Dict) -> None:
        """
        Constructor of SentinelAPI class.

        :param config_file: dictionary containing the settings
        :param data_file: dictionary containing the AOIs (GeoJSON)
        """

        super(SentinelAPI, self).__init__(config_file, data_file)

        self.config = None
        self.catalog = None
        self.instance_id = None
        self.sh_client_id = None
        self.sh_client_secret = None

        self.resolution = 10

        self.requests = dict()

        self.evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: [{
                        bands: ["B02", "B03", "B04", "B08"],
                        units: "DN"
                    }],
                    output: {
                        bands: 4,
                        sampleType: "INT16"
                    }
                };
            }

            function evaluatePixel(sample) {
                return [sample.B02, sample.B03, sample.B04, sample.B08];
            }
        """

    def login(self) -> None:
        """
        Logs into the API account.

        :return: None
        """

        self.sh_client_id = self.config_file["sentinel_sh_client_id"]
        self.instance_id = self.config_file["sentinel_instance_id"]
        self.sh_client_secret = self.config_file["sentinel_sh_client_secret"]

        self.config = SHConfig()
        self.config.sh_client_id = self.sh_client_id
        self.config.instance_id = self.instance_id
        self.config.sh_client_secret = self.sh_client_secret

        self.catalog = SentinelHubCatalog(config=self.config)

    def search(self, time_interval: Tuple[str, str], max_result_limit: int) -> None:
        """
        Searches the available images within the given time interval.

        :param time_interval: acquisition time interval of images
        :param max_result_limit: maximum number of results
        :return: None
        """

        self.requests.clear()

        for feature in self.data_file["features"]:
            bbox_coords = SentinelAPI.get_bbox_of_polygon(feature["geometry"]["coordinates"][0])

            bbox = BBox(bbox=bbox_coords, crs=CRS.POP_WEB)

            search_iterator = self.catalog.search(
                DataCollection.SENTINEL2_L2A,
                bbox=bbox,
                time=time_interval,
                query={"eo:cloud_cover": {"lte": int(self.config_file["max_cloud_cover"])}},
                fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover"], "exclude": []},
            )

            time_difference = dt.timedelta(hours=1)
            all_timestamps = search_iterator.get_timestamps()
            unique_acquisitions = filter_times(all_timestamps, time_difference)

            for timestamp in reversed(unique_acquisitions):
                data_folder = "/".join([self.config_file["download_dir_sentinel-2"],
                                        str(feature["properties"]["id"]),
                                        dt.datetime.strftime(timestamp, "%Y-%m-%d")])

                request = SentinelHubRequest(
                    data_folder=data_folder,
                    evalscript=self.evalscript,
                    input_data=[
                        SentinelHubRequest.input_data(
                            data_collection=DataCollection.SENTINEL2_L2A,
                            time_interval=(timestamp - time_difference, timestamp + time_difference),
                        )
                    ],
                    responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
                    bbox=bbox,
                    size=bbox_to_dimensions(bbox, resolution=self.resolution),
                    config=self.config,
                )

                if feature["properties"]["id"] not in self.requests.keys():
                    self.requests[feature["properties"]["id"]] = list()
                self.requests[feature["properties"]["id"]].append((timestamp, request))

                if len(self.requests[feature["properties"]["id"]]) == max_result_limit:
                    break

    def order(self) -> None:
        """
        Places the orders so that the unavailable images become available.

        :return: None
        """

        pass

    def download(self) -> None:
        """
        Downloads the available images.

        :return: None
        """

        for feature_id in self.requests.keys():
            for acquisition in self.requests[feature_id]:
                acquisition[1].save_data()
                print(feature_id)
                print(acquisition[1].get_filename_list()[0].split("\\")[0])

    @staticmethod
    def get_bbox_of_polygon(polygon_coords: List[List[int]]) -> List[int]:
        """
        Returns the bounding box of given polygon
        (bottom left, upper right coordinates).

        :param polygon_coords: List of polygon vertices.
        :return: the bounding box's bottom left and upper right coordinates
        """

        x_coords, y_coords = map(list, zip(*polygon_coords))
        return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
