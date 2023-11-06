import os
import copy
import json
import time
import pathlib
import requests

import datetime as dt

from baseapi import BaseAPI
from sentinelhub import filter_times
from requests.auth import HTTPBasicAuth
from typing import List, TypeVar, Tuple, Dict


TimeType = TypeVar("TimeType", dt.date, dt.datetime)


class PlanetAPI(BaseAPI):
    """
    API class for downloading Planet satellite images.

    """

    def __init__(self, config_file: Dict, data_file: Dict) -> None:
        """
        Constructor of PlanetAPI class.

        :param config_file: Dictionary containing the settings.
        :param data_file: Dictionary containing the AOIs (GeoJSON).
        """

        super(PlanetAPI, self).__init__(config_file, data_file)

        self.api_key = None
        self.search_url = None
        self.orders_url = None
        self.id_url = None
        self.item_type = None
        self.auth = None
        self.headers = None

        self.search_results = dict()
        self.order_urls = dict()

        self.successful_orders = list()

    def login(self) -> None:
        """
        Logs into the API account.

        :return: None
        """

        self.api_key = self.config_file["planet_api_key"]
        self.search_url = self.config_file["planet_search_url"]
        self.orders_url = self.config_file["planet_orders_url"]
        self.item_type = self.config_file["planet_item_type"]
        self.auth = HTTPBasicAuth(self.api_key, "")
        self.headers = {"content-type": "application/json"}

    def search(self, time_interval: Tuple[str, str], max_result_limit: int) -> None:
        """
        Searches the available images within the given time interval.

        :param time_interval: Acquisition time interval of images.
        :param max_result_limit: Maximum number of results.
        :return: None
        """

        for feature in self.data_file["features"]:
            geometry_filter = {
                "type": "GeometryFilter",
                "field_name": "geometry",
                "config": feature["geometry"],
            }

            date_range_filter = {
                "type": "DateRangeFilter",
                "field_name": "acquired",
                "config": {
                    "gte": time_interval[0] + "T00:00:00.000Z",
                    "lt": time_interval[1] + "T00:00:00.000Z",
                },
            }

            cloud_cover_filter = {
                "type": "RangeFilter",
                "field_name": "cloud_cover",
                "config": {"lte": float(self.config_file["max_cloud_cover"]) / 100},
            }

            geojson = self.start_search(
                self.item_type, geometry_filter, date_range_filter, cloud_cover_filter
            )

            feature_id = feature["properties"]["id"]
            time_difference = dt.timedelta(hours=12)
            image_ids = PlanetAPI.get_image_ids(geojson)
            unique_image_ids = PlanetAPI.get_unique_image_ids(
                image_ids, time_difference
            )

            self.search_results[feature_id] = unique_image_ids[:max_result_limit]

            self.search_results[feature_id] = self.filter_out_already_downloaded_images(
                feature_id, self.search_results[feature_id]
            )

    def order(self) -> None:
        """
        Places the orders so that the unavailable images become available.

        :return: None
        """

        for feature in self.data_file["features"]:
            for product in self.search_results[feature["properties"]["id"]]:
                products = [
                    {
                        "item_ids": [product],
                        "item_type": "PSScene",
                        "product_bundle": "analytic_sr_udm2",
                    }
                ]

                clip = {"clip": {"aoi": feature["geometry"]}}

                reproject = {"reproject": {"projection": "EPSG:3857"}}

                request_clip = {
                    "name": feature["properties"]["id"] + ": automated download",
                    "products": products,
                    "tools": [clip, reproject],
                }

                date_time_obj = dt.datetime.strptime(
                    "_".join(product.split("_")[:2]), "%Y%m%d_%H%M%S"
                )
                date_time_str = dt.datetime.strftime(date_time_obj, "%Y-%m-%d")

                order_url = self.place_order(request_clip)

                if feature["properties"]["id"] not in self.order_urls.keys():
                    self.order_urls[feature["properties"]["id"]] = dict()
                self.order_urls[feature["properties"]["id"]][date_time_str] = [
                    order_url,
                    "placed",
                ]

    def download(self, num_loops: int = 1000) -> None:
        """
        Downloads the available images.

        :param num_loops: Maximum number of iterations when waiting for order to be activated.
        :return: None
        """

        success_states = ["success", "partial"]

        count = 0
        all_ended = False

        while not all_ended and count < num_loops:
            all_ended = True

            for feature in self.order_urls.keys():
                for date in self.order_urls[feature]:
                    if self.order_urls[feature][date][1] in ["downloaded", "failed"]:
                        continue

                    order_id, order_state = self.get_state(
                        self.order_urls[feature][date][0]
                    )

                    if order_state in success_states:
                        success = self.download_order(
                            feature, date, self.order_urls[feature][date][0]
                        )
                        if not success:
                            time.sleep(2)
                            continue
                        self.order_urls[feature][date][1] = "downloaded"
                    elif order_state == "failed":
                        self.order_urls[feature][date][1] = "failed"
                    else:
                        all_ended = all_ended and False

                    time.sleep(2)

            if not all_ended:
                print("\nWaiting for downloads...\n")
                time.sleep(60)
                count += 1

    def start_search(
        self,
        item_type: str,
        geometry_filter: Dict,
        date_range_filter: Dict,
        cloud_cover_filter: Dict,
    ) -> Dict:
        """
        Starts the search for images based on the set filters.

        :param item_type: Item type of Planet satellite.
        :param geometry_filter: Filter for AOI.
        :param date_range_filter: Filter for acquisition date.
        :param cloud_cover_filter: Filter for cloud coverage.
        :return: Dictionary containing the search results.
        """

        combined_filter = {
            "type": "AndFilter",
            "config": [geometry_filter, date_range_filter, cloud_cover_filter],
        }

        # API request object
        search_request = {"item_types": [item_type], "filter": combined_filter}

        search_result = requests.post(
            self.search_url, auth=self.auth, json=search_request
        )

        geojson = search_result.json()

        return geojson

    def filter_out_already_downloaded_images(
        self, feature_id: str, image_ids: List[str]
    ) -> List[str]:
        """
        Filters out image ids that already exist locally.

        :param feature_id: The id property of a polygon (GeoJSON).
        :param image_ids: List of product ids.
        :return: Image ids that don't exist locally.
        """

        work_dir = "/".join(
            [
                self.config_file["workspace_root_dir"],
                self.config_file["download_dir_planetscope"],
                feature_id,
            ]
        )
        filtered_image_ids = copy.deepcopy(image_ids)

        dates = [
            dt.datetime.strftime(
                dt.datetime.strptime(
                    "_".join(product.split("_")[:2]),
                    "%Y%m%d_%H%M%S",
                ),
                "%Y-%m-%d",
            )
            for product in image_ids
        ]

        for _, dirnames, _ in os.walk(work_dir):
            for dirname in dirnames:
                if dirname in dates:
                    index = dates.index(dirname)
                    filtered_image_ids.remove(image_ids[index])

        return filtered_image_ids

    def place_order(self, request: Dict) -> str:
        """
        Places the order with set parameters.

        :param request: Dictionary containing the order request parameters.
        :return: The URL of the placed order.
        """

        response = requests.post(
            self.orders_url,
            data=json.dumps(request),
            auth=self.auth,
            headers=self.headers,
        )
        print(response)

        if not response.ok:
            raise Exception(response.content)

        order_id = response.json()["id"]
        print("Order id:", order_id)

        order_url = self.orders_url + "/" + order_id
        return order_url

    def get_state(self, order_url: str) -> Tuple[str, str]:
        """
        Returns the id and state of an order based on the given URL.

        :param order_url: The URL of an order.
        :return: Id and state of an order.
        """

        r = requests.get(order_url, auth=self.auth)
        response = r.json()
        order_state = response["state"]
        order_id = response["id"]

        print(order_id + ":", order_state)

        if order_state == "failed":
            raise Exception(response)

        return order_id, order_state

    def download_order(self, feature_id, date, order_url, overwrite=False) -> bool:
        """
        Downloads an order after it was processed.

        :param feature_id: The id property of a polygon (GeoJSON).
        :param date: Date of acquisition.
        :param order_url: The URL of an order.
        :param overwrite: Redownload image if True.
        :return: True if download succeeded, False if not.
        """

        r = requests.get(order_url, auth=self.auth)
        print(r)

        if r.status_code == 429:
            return False

        response = r.json()

        results = response["_links"]["results"]
        results_urls = [r["location"] for r in results]
        results_names = [r["name"] for r in results]

        data_folder = "/".join(
            [
                self.config_file["workspace_root_dir"],
                self.config_file["download_dir_planetscope"],
                str(feature_id),
                str(date),
            ]
        )

        results_paths = [
            pathlib.Path(os.path.join(data_folder, n)) for n in results_names
        ]
        print("{} items to download".format(len(results_urls)))

        for url, name, path in zip(results_urls, results_names, results_paths):
            if overwrite or not path.exists():
                print("downloading {}".format(name))
                r = requests.get(url, allow_redirects=True)
                path.parent.mkdir(parents=True, exist_ok=True)
                open(path, "wb").write(r.content)
            else:
                print("{} already exists, skipping...".format(name))
            time.sleep(2)

        return True

    @staticmethod
    def get_image_ids(geojson: Dict) -> List[str]:
        """
        Filters out image ids from search result.

        :param geojson: Dictionary containing the search results.
        :return: Image ids from the given search result.
        """

        image_ids = [feature["id"] for feature in geojson["features"]]
        return image_ids

    @staticmethod
    def get_unique_image_ids(
        image_ids: List[str], time_difference: dt.timedelta
    ) -> List[str]:
        """
        Returns image ids filtered out by the given time difference.

        :param image_ids: List of image ids.
        :param time_difference: Time difference between two acquisition dates.
        :return: List of image ids based on the time difference filter.
        """

        all_timestamps = list()
        all_unique_image_ids = list()

        for image_id in image_ids:
            date_time_str = "_".join(image_id.split("_")[:2])
            date_time_obj = dt.datetime.strptime(date_time_str, "%Y%m%d_%H%M%S")
            all_timestamps.append(date_time_obj)

        all_unique_timestamps = filter_times(all_timestamps, time_difference)

        for timestamp in all_unique_timestamps:
            date_time_str = dt.datetime.strftime(timestamp, "%Y%m%d_%H%M%S")
            match = [image_id for image_id in image_ids if date_time_str in image_id]
            all_unique_image_ids.append(match[0])

        all_unique_image_ids.reverse()

        return all_unique_image_ids
