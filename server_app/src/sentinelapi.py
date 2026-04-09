import datetime as dt
import rasterio

from server_app.src.baseapi import BaseAPI
from typing import Any, Dict, Tuple, List, Union
from model.persistence import Persistence
from pathlib import Path

from sentinelhub import (
    SHConfig,
    CRS,
    BBox,
    DataCollection,
    SentinelHubCatalog,
    MimeType,
    SentinelHubRequest,
    bbox_to_dimensions,
    filter_times,
)

# SentinelHub endpoint presets
SENTINELHUB_DEFAULT = "sentinelhub"
SENTINELHUB_CDSE = "cdse"

CDSE_BASE_URL = "https://sh.dataspace.copernicus.eu"
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"


class SentinelAPI(BaseAPI):
    """
    API class for downloading Sentinel-2 satellite images.

    Supports both the default SentinelHub and the Copernicus Data Space
    Ecosystem (CDSE) SentinelHub.  The backend is selected via the
    ``sentinel_hub_type`` configuration key (``"sentinelhub"`` or ``"cdse"``).
    """

    def __init__(self, settings: Persistence, data_file: Dict) -> None:
        """
        Constructor of SentinelAPI class.

        :param settings: Persistence object containing the settings.
        :param data_file: Dictionary containing the AOIs (GeoJSON).
        """

        super(SentinelAPI, self).__init__(settings, data_file)

        self.config = None
        self.catalog = None
        self.instance_id = None
        self.sh_client_id = None
        self.sh_client_secret = None

        self.download_results = []
        self.metadata_records = []

        self.resolution = 10

        self.requests = dict()

        # Determine which SentinelHub backend to use (default: sentinelhub)
        self.hub_type: str = getattr(settings, "sentinel_hub_type", SENTINELHUB_DEFAULT).lower()
        if self.hub_type not in (SENTINELHUB_DEFAULT, SENTINELHUB_CDSE):
            raise ValueError(
                f"Unknown sentinel_hub_type '{self.hub_type}'. "
                f"Must be '{SENTINELHUB_DEFAULT}' or '{SENTINELHUB_CDSE}'."
            )

        # Pre-build the data collection for the chosen backend
        self.data_collection = self._resolve_data_collection()

        self.evalscript = self.generate_evalscript(settings.masking, "swir" in settings.enabled_bands)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_data_collection(self) -> DataCollection:
        """Return the appropriate ``DataCollection`` for the configured hub type."""
        if self.hub_type == SENTINELHUB_CDSE:
            return DataCollection.SENTINEL2_L2A.define_from(
                "s2l2a_cdse",
                service_url=CDSE_BASE_URL,
            )
        return DataCollection.SENTINEL2_L2A

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def login(self) -> None:
        """
        Logs into the API account.

        Configures the ``SHConfig`` object for either the default
        SentinelHub or the CDSE SentinelHub, depending on ``self.hub_type``.

        :return: None
        """

        self.sh_client_id = self.settings.sentinel_sh_client_id
        self.sh_client_secret = self.settings.sentinel_sh_client_secret

        self.config = SHConfig()
        self.config.sh_client_id = self.sh_client_id
        self.config.sh_client_secret = self.sh_client_secret

        if self.hub_type == SENTINELHUB_CDSE:
            self.config.sh_base_url = CDSE_BASE_URL
            self.config.sh_token_url = CDSE_TOKEN_URL
        else:
            # Default SentinelHub requires an instance ID
            self.instance_id = self.settings.sentinel_instance_id
            self.config.instance_id = self.instance_id

        self.catalog = SentinelHubCatalog(config=self.config)

    def search(self, time_interval: Tuple[str, str], max_result_limit: int) -> None:
        """
        Searches the available images within the given time interval.

        :param time_interval: Acquisition time interval of images.
        :param max_result_limit: Maximum number of results.
        :return: None
        """

        self.requests.clear()

        for feature in self.data_file["features"]:
            bbox_coords = SentinelAPI.get_bbox_of_polygon(feature["geometry"]["coordinates"][0])

            bbox = BBox(bbox=bbox_coords, crs=CRS.POP_WEB)

            search_iterator = self.catalog.search(
                self.data_collection,
                bbox=bbox,
                time=time_interval,
                filter=f"eo:cloud_cover <= {int(self.settings.max_cloud_cover)}",
                fields={
                    "include": [
                        "id",
                        "properties.datetime",
                        "properties.eo:cloud_cover",
                    ],
                    "exclude": [],
                },
            )

            time_difference = dt.timedelta(hours=1)
            all_timestamps = search_iterator.get_timestamps()
            unique_acquisitions = filter_times(all_timestamps, time_difference)

            for timestamp in reversed(unique_acquisitions):
                data_folder = "/".join(
                    [
                        self.settings.workspace_root_dir,
                        self.settings.download_dir_sentinel_2,
                        str(feature["properties"]["id"]),
                        dt.datetime.strftime(timestamp, "%Y-%m-%d"),
                    ]
                )

                request = SentinelHubRequest(
                    data_folder=data_folder,
                    evalscript=self.evalscript,
                    input_data=[
                        SentinelHubRequest.input_data(
                            data_collection=self.data_collection,
                            time_interval=(
                                timestamp - time_difference,
                                timestamp + time_difference,
                            ),
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
        Orchestrates the download process and returns a report of metadata and
        stores the results in the `download_results` field.
        """
        for feature_id, requests in self.requests.items():
            for timestamp, request_obj in requests:
                try:
                    request_obj.save_data()
                    self.download_results.append((timestamp, request_obj))
                    filenames = request_obj.get_filename_list()
                    if filenames:
                        folder_name = Path(filenames[0]).parent.name
                        print(f"Successfully downloaded: {feature_id} -> {folder_name}")

                except Exception as e:
                    print(f"Error downloading {feature_id} at {timestamp}: {e}")
                    continue

    @staticmethod
    def generate_evalscript(masking: bool, with_swir: bool) -> str:
        """
        Generate evalscript. If masking is enabled, it downloads CLM band and evaluates the pixels based on its value

        :param masking: masking enabled
        :return: evalscipt to process sentinel data
        """
        bands = '["B02", "B03", "B04", "B08"'
        if with_swir:
            bands += ', "B12"'
        if masking:
            bands += ', "CLM"'
        bands += "]"
        if with_swir:
            clm_check = """
                        if (sample.CLM == 1) {
                        return [NaN, NaN, NaN, NaN, NaN];
                        }
                        """
        else:
            clm_check = """
                            if (sample.CLM == 1) {
                            return [NaN, NaN, NaN, NaN];
                            }
                            """
        if with_swir:
            evalscript = f"""
                        //VERSION=3
                        function setup() {{
                            return {{
                                input: [{{
                                    bands: {bands},
                                    units: "reflectance"
                                }}],
                                output: {{
                                    bands: 5,
                                    sampleType: "FLOAT32"
                                }}
                            }};
                        }}
        
                        function evaluatePixel(sample) {{
                            { clm_check if masking else ''}
                            return [sample.B02, sample.B03, sample.B04, sample.B08, sample.B12];
                        }}
                    """
        else:
            evalscript = f"""
                //VERSION=3
                function setup() {{
                    return {{
                        input: [{{
                            bands: {bands},
                            units: "reflectance"
                        }}],
                        output: {{
                            bands: 4,
                            sampleType: "FLOAT32"
                        }}
                    }};
                }}

                function evaluatePixel(sample) {{
                    { clm_check if masking else ''}
                    return [sample.B02, sample.B03, sample.B04, sample.B08];
                }}
            """
        return evalscript

    @staticmethod
    def get_bbox_of_polygon(polygon_coords: List[List[int]]) -> List[int]:
        """
        Returns the bounding box of given polygon
        (bottom left, upper right coordinates).

        :param polygon_coords: List of polygon vertices.
        :return: The bounding box's bottom left and upper right coordinates.
        """

        x_coords, y_coords = map(list, zip(*polygon_coords))
        return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
