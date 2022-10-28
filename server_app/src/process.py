import time
import json

import numpy as np
import datetime as dt

from model.model import Model
from pathlib import Path
from planetapi import PlanetAPI
from typing import Dict, Optional
from sentinelapi import SentinelAPI
from model.persistence import Persistence


class Process(object):
    """
    Class for automated waste detection.

    """

    def __init__(self) -> None:
        """
        Constructor of Process class.

        """

        super(Process, self).__init__()

        self.model = Model(Persistence())

        self.api = None
        self.processed_today = False
        self.pixel_size = None

        self.estimations = dict()

        if self.model.persistence.settings["SATELLITE_TYPE"].lower() == "PlanetScope".lower():
            self.api = PlanetAPI(self.model.persistence.settings, self.model.persistence.data_file)
            self.pixel_size = 3
        elif self.model.persistence.settings["SATELLITE_TYPE"].lower() == "Sentinel-2".lower():
            self.api = SentinelAPI(self.model.persistence.settings, self.model.persistence.data_file)
            self.pixel_size = 10

    def mainloop(self) -> None:
        """
        The main loop of the application. Starts new process and waits for the next.

        :return: None
        """

        self.startup()

        while True:
            self.process()
            secs = self.get_seconds_until_next_process()
            time.sleep(secs)

    def startup(self) -> None:
        """
        Executes the startup process: login, search, order, download earlier images.

        :return: None
        """

        print("{} Startup process started...".format(Process.timestamp()))

        yesterday_str = Process.get_sys_date_str(difference=-1)

        time_interval = self.model.persistence.settings["FIRST_SENTINEL-2_DATE"], yesterday_str
        observation_max_span = int(self.model.persistence.settings["OBSERVATION_SPAN_IN_DAYS"])

        print("{} Setting up the account...".format(Process.timestamp()))
        self.api.login()

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

        for feature_id in downloaded_images.keys():
            for date in downloaded_images[feature_id].keys():

                if feature_id in self.estimations.keys() and date in self.estimations[feature_id].keys():
                    continue

                path = downloaded_images[feature_id][date]

                indices_path = self.model.save_bands_indices(
                    self.model.persistence.settings["SATELLITE_TYPE"], path, "all",
                    "", "all", self.model.persistence.settings["FILE_EXTENSION"])

                low = int(self.model.persistence.settings["LOW_PROB_PERCENT"]) / 100
                medium = int(self.model.persistence.settings["MEDIUM_PROB_PERCENT"]) / 100
                high = int(self.model.persistence.settings["HIGH_PROB_PERCENT"]) / 100

                classified, heatmap = self.model.create_classification_and_heatmap_with_random_forest(
                    input_path=indices_path,
                    clf=self.model.persistence.clf,
                    low_medium_high_values=(low, medium, high),
                    garbage_c_id=int(self.model.persistence.settings["GARBAGE_C_ID"]) * 100,
                    working_dir="",
                    classification_postfix=self.model.persistence.settings["CLASSIFICATION_POSTFIX"],
                    heatmap_postfix=self.model.persistence.settings["HEATMAP_POSTFIX"],
                    file_extension=self.model.persistence.settings["FILE_EXTENSION"]
                )

                masked_classified, masked_heatmap = Model.create_masked_classification_and_heatmap(
                    original_input_path=indices_path,
                    classification_path=classified,
                    heatmap_path=heatmap,
                    garbage_c_id=int(self.model.persistence.settings["GARBAGE_C_ID"]) * 100,
                    water_c_id=int(self.model.persistence.settings["WATER_C_ID"]) * 100,
                    matrix=(
                        int(self.model.persistence.settings["MORPHOLOGY_MATRIX_SIZE"]),
                        int(self.model.persistence.settings["MORPHOLOGY_MATRIX_SIZE"])
                    ),
                    iterations=int(self.model.persistence.settings["MORPHOLOGY_ITERATIONS"]),
                    working_dir="",
                    classification_postfix=self.model.persistence.settings["MASKED_CLASSIFICATION_POSTFIX"],
                    heatmap_postfix=self.model.persistence.settings["MASKED_HEATMAP_POSTFIX"],
                    file_extension=self.model.persistence.settings["FILE_EXTENSION"]
                )

                pixel_size_x, pixel_size_y = None, None
                if self.model.persistence.settings["SATELLITE_TYPE"].lower() == "PlanetScope".lower():
                    pixel_size_x = pixel_size_y = 3
                elif self.model.persistence.settings["SATELLITE_TYPE"].lower() == "Sentinel-2".lower():
                    pixel_size_x = pixel_size_y = 10

                estimation = Model.estimate_garbage_area(
                    input_path=masked_classified,
                    image_type="classified",
                    garbage_c_id=int(self.model.persistence.settings["GARBAGE_C_ID"]),
                    pixel_sizes=(pixel_size_x, pixel_size_y)
                )

                if feature_id not in self.estimations.keys():
                    self.estimations[feature_id] = dict()
                self.estimations[feature_id][date] = estimation

        with open(self.model.persistence.settings["ESTIMATIONS_FILE_PATH"], "w") as file:
            json.dump(self.estimations, file, indent=4)

    def get_seconds_until_next_process(self) -> float:
        """
        Calculates remaining seconds until a new process should be started.

        :return: remaining seconds until next process
        """

        reset_time = self.model.persistence.settings["DOWNLOAD_START_TIME"]
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

        days = int(self.model.persistence.settings["OBSERVATION_SPAN_IN_DAYS"])

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

    def get_satellite_images(self) -> Dict:
        """
        Returns the paths of downloaded images.

        :return: dictionary containing the paths
        """

        sentinel_path = self.model.persistence.settings["DOWNLOAD_DIR_SENTINEL-2"]
        planet_path = self.model.persistence.settings["DOWNLOAD_DIR_PLANETSCOPE"]
        satellite_type = self.model.persistence.settings["SATELLITE_TYPE"]

        images = None

        if satellite_type.lower() == "Sentinel-2".lower():
            images = Process.find_images(sentinel_path, "response.tiff")
        elif satellite_type.lower() == "PlanetScope".lower():
            images = Process.find_images(planet_path, "*AnalyticMS_SR_clip.tif")

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

    @staticmethod
    def find_images(dir_path: str, file_name_postfix: str) -> Dict:
        """
        Returns the paths of files in the given directory.

        :param dir_path: root directory of the search
        :param file_name_postfix: file name postfix of wanted files
        :return: dictionary containing the paths of files
        """

        images = dict()

        for path in Path(dir_path).rglob(file_name_postfix):
            abs_path = str(path.resolve())
            rel_path = str(path.relative_to(dir_path))
            split_rel_path = rel_path.split("\\")
            feature_id = split_rel_path[0]
            date = split_rel_path[1]

            if feature_id not in images.keys():
                images[feature_id] = dict()
            images[feature_id][date] = "/".join(abs_path.split("\\"))

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
