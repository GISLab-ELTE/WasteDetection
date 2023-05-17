import os
import time
import json
import pickle
import fnmatch
import geojson
import jsonmerge

import numpy as np
import datetime as dt

from model import Model
from pathlib import Path
from planetapi import PlanetAPI
from typing import Dict, Optional
from collections import OrderedDict
from sentinelapi import SentinelAPI
from sklearn.ensemble import RandomForestClassifier


class Process(object):
    """
    Class for automated waste detection.

    """

    def __init__(self) -> None:
        """
        Constructor of Process class.

        """

        super(Process, self).__init__()

        self.config_sample_name = "../resources/config.sample.json"
        self.config_local_name = "../resources/config.local.json"

        self.config_file = self.load_config_file()
        self.data_file = self.load_data_file()
        self.clf = self.load_clf()

        self.model = Model(self.config_file)

        self.api = None
        self.processed_today = False
        self.pixel_size = None

        self.estimations = dict()

        self.satellite_type = self.config_file["satellite_type"]

        if self.satellite_type.lower() == "PlanetScope".lower():
            self.api = PlanetAPI(self.config_file, self.data_file)
            self.pixel_size = 3
        elif self.satellite_type.lower() == "Sentinel-2".lower():
            self.api = SentinelAPI(self.config_file, self.data_file)
            self.pixel_size = 10

        self.api.data_file = Model.convert_multipolygons_to_polygons(self.api.data_file)

        if self.satellite_type.lower() == "Sentinel-2".lower():
            self.api.data_file = Model.transform_coordinates_to_epsg_3857(self.api.data_file)

    def mainloop(self, run_startup: bool, run_sleep: bool) -> None:
        """
        The main loop of the application. Starts new process and waits for the next.

        :return: None
        """

        print("{} Setting up the account...".format(Process.timestamp()))
        self.api.login()

        if run_startup:
            self.startup()

        if run_sleep:
            while True:
                self.process()
                secs = self.get_seconds_until_next_process()
                time.sleep(secs)
        else:
            self.process()

    def startup(self) -> None:
        """
        Executes the startup process: login, search, order, download earlier images.

        :return: None
        """

        print("{} Startup process started...".format(Process.timestamp()))

        yesterday_str = Process.get_sys_date_str(difference=-1)

        time_interval = self.config_file["first_sentinel-2_date"], yesterday_str
        observation_max_span = int(self.config_file["observation_span_in_days"])

        print("{} Searching for earlier images...".format(Process.timestamp()))
        self.api.search(time_interval, observation_max_span)

        print("{} Placing orders for earlier images...".format(Process.timestamp()))
        self.api.order()

        print("{} Started downloading earlier images...".format(Process.timestamp()))
        self.api.download()
        print("{} Finished downloading earlier images...".format(Process.timestamp()))

        print("\nALERT\nAcquisition dates:\n")
        self.print_acquisition_dates(observation_max_span)

        print("{} Startup process ended...".format(Process.timestamp()))

    def process(self) -> None:
        """
        Executes a new process: search, order, download, estimate.

        :return: None
        """

        sys_date_today = Process.get_sys_date_str()
        sys_date_yesterday = Process.get_sys_date_str(difference=-1)
        max_num_of_results = 1

        time_interval = sys_date_yesterday, sys_date_today

        print("{} Process started...".format(Process.timestamp()))

        print("{} Searching for new images...".format(Process.timestamp()))
        self.api.search(time_interval, max_num_of_results)

        print("{} Placing orders for available images...".format(Process.timestamp()))
        self.api.order()

        print("{} Started downloading images...".format(Process.timestamp()))

        success = False
        while not success:
            try:
                self.api.download()
            except Exception:
                pass
            else:
                success = True

        print("{} Finished downloading images...".format(Process.timestamp()))

        print("\nALERT\nAcquisition dates:\n")
        self.print_acquisition_dates(max_num_of_results)

        print("{} Estimating extent of polluted areas...".format(Process.timestamp()))
        self.create_estimations()
        print("{} Finished estimation...".format(Process.timestamp()))

        print("{} Analyzing acquired data...".format(Process.timestamp()))
        self.analyze_estimations()
        print("{} Finished analyzing data...".format(Process.timestamp()))

        print("{} Process finished...".format(Process.timestamp()))

        print("{} Awaiting execution of next process...".format(Process.timestamp()))

    def create_estimations(self) -> None:
        """
        Executes the estimations on new images.

        :return: None
        """

        downloaded_images = self.get_satellite_images()
        sentinel_path = self.config_file["result_dir_sentinel-2"]
        planet_path = self.config_file["result_dir_planetscope"]
        satellite_type = self.config_file["satellite_type"]
        work_dir = sentinel_path if satellite_type.lower() == "Sentinel-2".lower() else planet_path

        for feature_id in downloaded_images.keys():
            for date in downloaded_images[feature_id].keys():

                if feature_id in self.estimations.keys() and date in self.estimations[feature_id].keys():
                    continue

                path = downloaded_images[feature_id][date]
                dir_name = os.path.dirname(path)
                masked_heatmap_postfix = self.config_file["masked_heatmap_postfix"]

                processed = False
                for file in os.listdir(dir_name):
                    if fnmatch.fnmatch(file, f"*{masked_heatmap_postfix}*"):
                        processed = True
                        break

                if processed:
                    continue

                indices_path = self.model.save_bands_indices(path, "all", "all")

                classified, heatmap = self.model.create_classification_and_heatmap_with_random_forest(
                    indices_path, self.clf
                )

                masked_classified, masked_heatmap = self.model.create_masked_classification_and_heatmap(
                    indices_path, classified, heatmap
                )

                Model.get_waste_geojson(
                    input_file=masked_classified,
                    output_file="/".join([work_dir, feature_id, date, "classified.geojson"]),
                    search_value=100
                )

                heatmap_types = [("low", 1), ("medium", 2), ("high", 3)]
                for heatmap_type, value in heatmap_types:
                    Model.get_waste_geojson(
                        input_file=masked_heatmap,
                        output_file="/".join([work_dir, feature_id, date, heatmap_type + ".geojson"]),
                        search_value=value
                    )

                estimation = self.model.estimate_garbage_area(masked_classified, "classified")

                if feature_id not in self.estimations.keys():
                    self.estimations[feature_id] = dict()
                self.estimations[feature_id][date] = estimation

        with open(self.config_file["estimations_file_path"], "w") as file:
            json.dump(self.estimations, file, indent=4)

        geojson_files = self.find_geojson_files(work_dir)
        narrowed_geojson_files = OrderedDict()
        observation_span_in_days = int(self.config_file["observation_span_in_days"])

        for key, value in geojson_files.items():
            narrowed_geojson_files[key] = OrderedDict(list(value.items())[-observation_span_in_days:])

        with open(self.config_file["geojson_files_path"], "w") as file:
            json.dump(narrowed_geojson_files, file, indent=4)

    def get_seconds_until_next_process(self) -> float:
        """
        Calculates remaining seconds until a new process should be started.

        :return: remaining seconds until next process
        """

        reset_time = self.config_file["download_start_time"]
        reset_time_obj = dt.datetime.strptime(reset_time, "%H:%M:%S")
        hour, minute, second = reset_time_obj.hour, reset_time_obj.minute, reset_time_obj.second

        today = dt.datetime.today()
        tomorrow = today.replace(day=today.day, hour=hour, minute=minute,
                                 second=second, microsecond=0) + dt.timedelta(days=1)

        delta_t = tomorrow - today
        secs = delta_t.total_seconds()

        return secs

    def analyze_estimations(self) -> None:
        """
        Calculates the mean of the polluted areas' extension in the previous X days, compares the latest estimations to
        this value and prints the results of analysis to the console.

        :return: None
        """

        days = int(self.config_file["observation_span_in_days"])

        for feature_id in self.estimations.keys():
            sorted_dates = sorted(self.estimations[feature_id].keys(), reverse=True)
            dates_to_use = sorted_dates[:days]
            estimations = [self.estimations[feature_id][date] for date in dates_to_use]

            mean = np.mean(estimations[1:])
            latest_estimation = estimations[0]

            if mean == 0:
                print("There is not enough data to analyze!")
                continue

            difference = round((latest_estimation / mean - 1.0) * 100, 2)

            print("\n{}".format(feature_id))
            print("Latest acquisition date: {}".format(dates_to_use[0]))
            print("Latest estimation: {}".format(latest_estimation))
            print("Mean of the previous {} acquired days: {}".format(days - 1, mean))

            if difference > 0:
                print("{}% more polluted area than the estimated mean.".format(difference))
            elif difference < 0:
                print("{}% less polluted area than the estimated mean.".format(-1 * difference))
            else:
                print("Area of polluted area is exactly the same as the estimated mean.")

        print()

    def get_satellite_images(self) -> OrderedDict:
        """
        Returns the paths of downloaded images.

        :return: dictionary containing the paths
        """

        sentinel_path = self.config_file["download_dir_sentinel-2"]
        planet_path = self.config_file["download_dir_planetscope"]
        satellite_type = self.config_file["satellite_type"]

        images = None

        if satellite_type.lower() == "Sentinel-2".lower():
            images = Process.find_files(sentinel_path, "response.tiff")
        elif satellite_type.lower() == "PlanetScope".lower():
            images = Process.find_files(planet_path, "*AnalyticMS_SR_clip_reproject.tif")

        return images

    def print_acquisition_dates(self, observation_max_span: int) -> None:
        """
        Prints the last X dates of the acquisitions to the console.

        :param observation_max_span: max number of dates to be printed
        :return: None
        """

        downloaded_images = self.get_satellite_images()

        for feature_id in downloaded_images.keys():
            print("{}:".format(feature_id))
            for date in list(downloaded_images[feature_id].keys())[-observation_max_span:]:
                print(date)
            print()

    def load_config_file(self) -> Dict:
        """
        Loads config file for later use.

        :return: the loaded config file in Dict form
        """

        with open(self.config_sample_name, "r") as file:
            config_sample = json.load(file)

        if os.path.exists(self.config_local_name):
            with open(self.config_local_name, "r") as file:
                config_local = json.load(file)

            config_file = jsonmerge.merge(config_sample, config_local)
            return config_file
        else:
            return config_sample

    def load_data_file(self) -> Dict:
        """
        Loads the data file (GeoJSON) that contains the AOIs for later use.

        :return: the loaded data file in Dict form
        """

        with open(self.config_file["data_file_path"], "r") as file:
            geojson_file = geojson.load(file)
        return geojson_file

    def load_clf(self) -> RandomForestClassifier:
        """
        Loads the classifier for later use.

        :return: the loaded classifier
        """

        with open(self.config_file["clf_path"], "rb") as file:
            clf = pickle.load(file)
        return clf

    def find_geojson_files(self, dir_path: str) -> Dict:
        """
        Find relative GeoJSON file paths.

        :param dir_path: root directory of the search
        :return: dictionary containing the relative paths of files
        """

        geojson_files = Process.find_files(dir_path, "*.geojson", only_one=False)

        rel_path_start_dir = os.path.dirname(self.config_file["geojson_files_path"])
        for outer_key, outer_value in geojson_files.items():
            for inner_key, inner_value in outer_value.items():
                for i in range(len(inner_value)):
                    rel_path = os.path.relpath(inner_value[i], start=rel_path_start_dir)
                    rel_path = rel_path.replace("\\", "/")
                    geojson_files[outer_key][inner_key][i] = rel_path

        return geojson_files

    @staticmethod
    def find_files(dir_path: str, file_name_postfix: str, only_one: bool = True) -> OrderedDict:
        """
        Returns the paths of files in the given directory.

        :param dir_path: root directory of the search
        :param file_name_postfix: file name postfix of wanted files
        :param only_one: only one result or all
        :return: dictionary containing the absolute paths of files
        """

        images = OrderedDict()

        for path in sorted(Path(dir_path).rglob(file_name_postfix)):
            rel_path = str(path.relative_to(dir_path))
            rel_path = rel_path.replace("\\", "/")
            split_rel_path = rel_path.split("/")
            feature_id = split_rel_path[0]
            date = split_rel_path[1]

            if feature_id not in images.keys():
                images[feature_id] = OrderedDict()

            if only_one:
                images[feature_id][date] = "/".join([dir_path] + rel_path.split("/"))
            else:
                if date not in images[feature_id].keys():
                    images[feature_id][date] = list()
                images[feature_id][date].append("/".join([dir_path] + rel_path.split("/")))

        return images

    @staticmethod
    def get_sys_date_str(difference: Optional[int] = 0) -> str:
        """
        Returns a date as a string: actual date + difference.

        :param difference:  the difference added to today's date:
                            difference = -1 -> yesterday,
                            difference =  1  -> tomorrow
        :return: date as a string
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

        :param date_obj: date object
        :param format_str: output format string
        :return: string format of date object
        """

        date_str = dt.datetime.strftime(date_obj, format_str)
        return date_str

    @staticmethod
    def timestamp() -> str:
        """
        Returns the system date and time: e.g. 2000-06-26 13:36:00.

        :return: system date and time in string format
        """
        return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
