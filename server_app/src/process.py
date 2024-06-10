import os
import json
import fnmatch
import logging

import numpy as np
import datetime as dt

from pathlib import Path
from model.model import Model
from typing import List, Optional
from collections import OrderedDict
from server_app.src.planetapi import PlanetAPI
from server_app.src.sentinelapi import SentinelAPI


class Process(object):
    """
    Class for automated waste detection.

    """

    def __init__(self, model: Model, download_init: bool, download_update: bool, classify: bool) -> None:
        """
        Constructor of Process class.

        :param classify: whether to run classification instead of download or not.
        """

        super(Process, self).__init__()

        self.model = model

        self.api = None
        self.pixel_size = None
        self.download_init = download_init
        self.download_update = download_update
        self.classify = classify

        self.estimations = dict()

        self.satellite_type = self.model.persistence.satellite_type.lower()

        if self.satellite_type == "planetscope":
            self.api = PlanetAPI(self.model.persistence, self.model.persistence.data_file)
            self.pixel_size = 3
        elif self.satellite_type == "sentinel-2":
            self.api = SentinelAPI(self.model.persistence, self.model.persistence.data_file)
            self.pixel_size = 10

        self.api.data_file = Model.convert_multipolygons_to_polygons(self.api.data_file)

        if self.satellite_type == "sentinel-2":
            self.api.data_file = Model.transform_dict_of_coordinates_to_crs(
                data_file=self.api.data_file, crs_to="epsg:3857"
            )

    def mainloop(self) -> None:
        """
        The main loop of the application. Starts new process and waits for the next.

        :return: None
        """

        if not self.classify and not self.download_init and not self.download_update:
            logging.error("One of the flags must be specified. See help.")
            return

        if self.download_init and self.download_update:
            logging.error("cannot have download-init and download-update at the same time!")
            return

        if not self.classify:
            logging.info("Started setting up the account.")
            self.api.login()
            logging.info("Finished setting up the account.")
        else:
            self.execute_classification()

        if self.download_init:
            self.startup()
        elif self.download_update:
            self.execute_download_pipeline()

    def startup(self) -> None:
        """
        Executes the startup process: login, search, order, download earlier images.

        :return: None
        """

        logging.info("Startup process started.")

        yesterday_str = Process.get_sys_date_str(difference=-1)

        time_interval = self.model.persistence.first_sentinel_2_date, yesterday_str
        observation_max_span = self.model.persistence.observation_span_in_days

        logging.info("Searching for earlier images.")
        self.api.search(time_interval, observation_max_span)

        logging.info("Placing orders for earlier images.")
        self.api.order()

        logging.info("Started downloading earlier images.")
        self.api.download()
        logging.info("Finished downloading earlier images.")

        logging.warning("\nALERT\nAcquisition dates:\n")
        self.print_acquisition_dates(observation_max_span)

        logging.info("Startup process ended.")

    def execute_classification(self) -> None:
        """
        Executes a classification: Creates and analyzes estimations on new images.

        :return: None
        """

        logging.info("{} Estimating extent of polluted areas...")
        self.create_estimations()
        logging.info("{} Finished estimation...")

        logging.info("{} Analyzing acquired data...")
        self.analyze_estimations()
        logging.info("{} Finished analyzing data...")

    def execute_download_pipeline(self) -> None:
        """
        Executes the download pipeline: searches, orders and downloads new images.

        :return: None
        """

        sys_date_today = Process.get_sys_date_str()
        sys_date_yesterday = Process.get_sys_date_str(difference=-1)
        max_num_of_results = 1

        time_interval = sys_date_yesterday, sys_date_today

        logging.info("Main process started.")

        logging.info("Searching for new images.")
        self.api.search(time_interval, max_num_of_results)

        logging.info("Placing orders for available images.")
        self.api.order()

        logging.info("Started downloading images.")

        success = False
        while not success:
            try:
                self.api.download()
            except Exception as e:
                logging.error(str(e))
                pass
            else:
                success = True

        logging.info("Finished downloading images.")

        logging.warning("\nALERT\nAcquisition dates:\n")
        self.print_acquisition_dates(max_num_of_results)

    def create_estimations(self) -> None:
        """
        Executes the estimations on new images.

        :return: None
        """

        downloaded_images = self.get_satellite_images()
        sentinel_path = self.join_path("workspace_root_dir", "result_dir_sentinel_2")
        planet_path = self.join_path("workspace_root_dir", "result_dir_planetscope")
        work_dir = sentinel_path if self.satellite_type == "sentinel-2" else planet_path

        for feature_id in downloaded_images.keys():
            for date in downloaded_images[feature_id].keys():
                output_dir_path = "/".join([work_dir, feature_id, date])
                masked_heatmap_postfix = self.model.persistence.masked_heatmap_postfix

                processed = False

                if not os.path.exists(output_dir_path):
                    os.makedirs(output_dir_path)

                for file in os.listdir(output_dir_path):
                    if fnmatch.fnmatch(file, f"*{masked_heatmap_postfix}*"):
                        processed = True
                        break

                if processed:
                    continue

                input_file_path = downloaded_images[feature_id][date]
                indices_path = self.model.save_bands_indices(input_file_path, "all", "all", output_dir_path)

                (classified, heatmap) = self.model.create_classification_and_heatmap_with_random_forest(
                    indices_path,
                    self.model.persistence.clf,
                    self.model.persistence.classification_postfix,
                    self.model.persistence.heatmap_postfix,
                )

                (masked_classified, masked_heatmap) = self.model.create_masked_classification_and_heatmap(
                    indices_path,
                    classified,
                    heatmap,
                    self.model.persistence.masked_classification_postfix,
                    self.model.persistence.masked_heatmap_postfix,
                )

                Model.get_waste_geojson(
                    input_file=masked_classified,
                    output_file="/".join([work_dir, feature_id, date, "classified.geojson"]),
                    search_value=100,
                )

                heatmap_types = [("low", 1), ("medium", 2), ("high", 3)]
                for heatmap_type, value in heatmap_types:
                    Model.get_waste_geojson(
                        input_file=masked_heatmap,
                        output_file="/".join([work_dir, feature_id, date, heatmap_type + ".geojson"]),
                        search_value=value,
                    )

                estimation = self.model.estimate_garbage_area(masked_classified, "classified")

                if feature_id not in self.estimations.keys():
                    self.estimations[feature_id] = dict()
                self.estimations[feature_id][date] = estimation

        self.generate_json_files_for_webapp()

    def generate_json_files_for_webapp(self) -> None:
        """
        Generates all the needed JSON files for web_app.

        """

        geojson_files_path = self.join_path("workspace_root_dir", "geojson_files_path")
        satellite_images_path = self.join_path("workspace_root_dir", "satellite_images_path")
        estimations_file_path = self.join_path("workspace_root_dir", "estimations_file_path")

        result_dir, image_files_abs, image_files_rel = None, None, None

        if self.satellite_type == "sentinel-2":
            download_dir = self.join_path("workspace_root_dir", "download_dir_sentinel_2")
            result_dir = self.join_path("workspace_root_dir", "result_dir_sentinel_2")
            image_files_abs = Process.find_files_absolute(download_dir, "response.tiff")
            image_files_rel = Process.find_files_relative(
                download_dir,
                "response.tiff",
                relative_to=os.path.dirname(satellite_images_path),
            )
        elif self.satellite_type == "planetscope":
            download_dir = self.join_path("workspace_root_dir", "download_dir_planetscope")
            result_dir = self.join_path("workspace_root_dir", "result_dir_planetscope")
            image_files_abs = Process.find_files_absolute(download_dir, "*AnalyticMS_SR_clip_reproject.tif")
            image_files_rel = Process.find_files_relative(
                download_dir,
                "*AnalyticMS_SR_clip_reproject.tif",
                relative_to=os.path.dirname(satellite_images_path),
            )

        geojson_files_rel = Process.find_files_relative(
            result_dir, "*.geojson", relative_to=os.path.dirname(geojson_files_path)
        )

        image_dict = OrderedDict()
        geojson_dict = OrderedDict()

        for i in range(len(image_files_abs)):
            rel_path_split = image_files_rel[i].split("/")

            feature_id = rel_path_split[1]
            date = rel_path_split[2]

            min_value, max_value = self.model.get_min_max_value_of_band(image_files_abs[i], 3)

            if feature_id not in image_dict:
                image_dict[feature_id] = OrderedDict()

            if date not in image_dict[feature_id]:
                image_dict[feature_id][date] = OrderedDict()

            image_dict[feature_id][date]["src"] = image_files_rel[i]
            image_dict[feature_id][date]["min"] = int(min_value)
            image_dict[feature_id][date]["max"] = int(max_value)

        for file in geojson_files_rel:
            rel_path_split = file.split("/")

            feature_id = rel_path_split[1]
            date = rel_path_split[2]

            if feature_id not in geojson_dict:
                geojson_dict[feature_id] = OrderedDict()

            if date not in geojson_dict[feature_id]:
                geojson_dict[feature_id][date] = list()

            geojson_dict[feature_id][date].append(file)

        with open(satellite_images_path, "w") as file:
            json.dump(image_dict, file, indent=4)

        self.add_model_data_to_json_file(geojson_files_path, geojson_dict)
        self.add_model_data_to_json_file(estimations_file_path, self.estimations)

    def add_model_data_to_json_file(self, file_path: str, model_data: OrderedDict) -> None:
        """
        Adds data related to the model to the given json file.
        The key of the data will be the id of the classification model.
        If the file does not exist or is empty, it will be created and/or initialized properly.

        :param file_path: The path of the json file
        :param model_data: The dictionary that needs to be added to the json file.
        """

        clf_id = self.model.persistence.clf_id

        # to prevent deleting the file's contents before reading, we need to use the "r" flag to read the contents.
        # This throws an exception when the file does not exist, thus we need to create an empty json file to prevent errors.
        if (not os.path.exists(file_path)) or os.stat(file_path).st_size == 0:
            with open(file_path, "w") as file:
                json.dump({}, file, indent=4)

        with open(file_path, "r") as file:
            estimations_file_content = json.load(file)

        with open(file_path, "w") as file:
            estimations_file_content[clf_id] = model_data
            json.dump(estimations_file_content, file, indent=4)

    def join_path(self, key_1: str, key_2: str) -> str:
        """
        Joins paths of config file based on their keys.

        :param key_1: Key of first value.
        :param key_2: Key of second value.
        :return: The joined path.
        """

        path = os.path.join(
            getattr(self.model.persistence, key_1),
            getattr(self.model.persistence, key_2),
        ).replace("\\", "/")
        return path

    def analyze_estimations(self) -> None:
        """
        Calculates the mean of the polluted areas' extension in the previous X days, compares the latest estimations to
        this value and prints the results of analysis to the console.

        :return: None
        """

        days = self.model.persistence.observation_span_in_days

        for feature_id in self.estimations.keys():
            sorted_dates = sorted(self.estimations[feature_id].keys(), reverse=True)
            dates_to_use = sorted_dates[:days]
            estimations = [self.estimations[feature_id][date] for date in dates_to_use]

            mean = np.mean(estimations[1:])
            latest_estimation = estimations[0]

            if mean == 0:
                logging.error("There is not enough data to analyze!")
                continue

            difference = round((latest_estimation / mean - 1.0) * 100, 2)

            logging.info(feature_id)
            logging.info(f"Latest acquisition date: {dates_to_use[0]}")
            logging.info(f"Latest estimation: {latest_estimation}")
            logging.info(f"Mean of the previous {days - 1} acquired days: {mean}")

            if difference > 0:
                logging.info(f"{difference}% more polluted area than the estimated mean.")
            elif difference < 0:
                logging.info(f"{-1 * difference}% less polluted area than the estimated mean.")
            else:
                logging.info("Area of polluted area is exactly the same as the estimated mean.")

        print()

    def print_acquisition_dates(self, observation_max_span: int) -> None:
        """
        Prints the last X dates of the acquisitions to the console.

        :param observation_max_span: Max number of dates to be printed.
        :return: None
        """

        downloaded_images = self.get_satellite_images()

        for feature_id in downloaded_images.keys():
            print("{}:".format(feature_id))
            for date in list(downloaded_images[feature_id].keys())[-observation_max_span:]:
                print(date)
            print()

    def get_satellite_images(self) -> OrderedDict:
        """
        Returns the paths of downloaded images.

        :return: Dictionary containing the paths.
        """

        sentinel_path = self.join_path("workspace_root_dir", "download_dir_sentinel_2")
        planet_path = self.join_path("workspace_root_dir", "download_dir_planetscope")

        download_dir = sentinel_path if self.satellite_type == "sentinel-2" else planet_path
        pattern = "response.tiff" if self.satellite_type == "sentinel-2" else "*AnalyticMS_SR_clip_reproject.tif"

        files = Process.find_files_absolute(download_dir, pattern)
        images = OrderedDict()

        for file in files:
            split_str = file.replace(download_dir, "")
            split_str = list(filter(None, split_str.split("/")))
            feature_id = split_str[0]
            date = split_str[1]

            if feature_id not in images:
                images[feature_id] = OrderedDict()

            images[feature_id][date] = file

        return images

    @staticmethod
    def find_files_absolute(root_dir: str, pattern: str) -> List[str]:
        """
        Finds the absolute path of files recursively in root_dir that matches the given pattern.

        :param root_dir: Root directory of the search.
        :param pattern: Pattern for filenames.
        :return: List of absolute paths.
        """

        files = sorted([os.path.abspath(path).replace("\\", "/") for path in Path(root_dir).rglob(pattern)])
        return files

    @staticmethod
    def find_files_relative(root_dir: str, pattern: str, relative_to: str) -> List[str]:
        """
        Finds the path of files recursively in root_dir that matches the given pattern.
        The results will be relative to given directory.

        :param root_dir: Root directory of the search.
        :param pattern: Pattern for filenames.
        :param relative_to: Results will be relative to this directory.
        :return: List of relative paths.
        """

        files = Process.find_files_absolute(root_dir, pattern)
        files = [os.path.relpath(file, start=relative_to).replace("\\", "/") for file in files]
        return files

    @staticmethod
    def get_sys_date_str(difference: Optional[int] = 0) -> str:
        """
        Returns a date as a string: actual date + difference.

        :param difference:  The difference added to today's date:
                            difference = -1 -> yesterday,
                            difference =  1  -> tomorrow.
        :return: Date as a string.
        """

        sys_date_obj = dt.date.today()
        difference_obj = dt.timedelta(days=abs(difference))

        if difference < 0:
            new_date_obj = sys_date_obj - difference_obj
        elif difference > 0:
            new_date_obj = sys_date_obj + difference_obj
        else:
            new_date_obj = sys_date_obj

        date_str = Process.get_date_str(new_date_obj, "%Y-%m-%d")
        return date_str

    @staticmethod
    def get_date_str(date_obj: dt.date, format_str: str) -> str:
        """
        Returns a date as a string based on the given format.

        :param date_obj: Date object.
        :param format_str: Output format string.
        :return: String format of date object.
        """

        date_str = dt.datetime.strftime(date_obj, format_str)
        return date_str
