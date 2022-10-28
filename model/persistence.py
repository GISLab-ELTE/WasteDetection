import os
import json
import pickle
import geojson

from typing import Dict, Union
from model.exceptions import *
from sklearn.ensemble import RandomForestClassifier


# constants
CONFIG_FILE_NAME = "config.json"


class Persistence(object):
    """
    A class that is the Persistence layer of the application. Its purpose is to load and save data.

    """

    def __init__(self):
        """
        The constructor of the Persistence class.

        """

        self._config_file = CONFIG_FILE_NAME
        self._settings = None
        self.data_file = None
        self.clf = None

        self.satellite_type = None
        self.working_dir = None
        self.file_extension = None
        self.hotspot_rf_path = None
        self.floating_rf_path = None
        self.morphology_matrix_size = None
        self.morphology_iterations = None
        self.washed_up_heatmap_sections = None
        self.heatmap_high_prob = None
        self.heatmap_medium_prob = None
        self.heatmap_low_prob = None
        self.hotspot_classified_postfix = None
        self.hotspot_heatmap_postfix = None
        self.floating_classified_postfix = None
        self.floating_heatmap_postfix = None
        self.floating_masked_classified_postfix = None
        self.floating_masked_heatmap_postfix = None
        self.washed_up_before_postfix = None
        self.washed_up_after_postfix = None
        self.training_label_blue = None
        self.training_label_green = None
        self.training_label_red = None
        self.training_label_nir = None
        self.training_label_pi = None
        self.training_label_ndwi = None
        self.training_label_ndvi = None
        self.training_label_rndvi = None
        self.training_label_sr = None
        self.training_estimators = None
        self.garbage_mc_id = None
        self.water_mc_id = None
        self.planet_blue_band = None
        self.planet_green_band = None
        self.planet_red_band = None
        self.planet_nir_band = None
        self.sentinel_blue_band = None
        self.sentinel_green_band = None
        self.sentinel_red_band = None
        self.sentinel_nir_band = None
        self.colors = list()

        self.load_constants()

    # Class properties
    @property
    def settings(self) -> Dict[str, str]:
        return self._settings

    # Non-static public methods
    def load_constants(self) -> None:
        """
        Loads the saved data and sets the values of the data members.

        :return: None
        """

        try:
            self._settings = Persistence._load_settings(self._config_file)

            if self.get_value("DATA_FILE_PATH"):
                self.data_file = Persistence._load_data_file(self.settings["DATA_FILE_PATH"])

            if self.get_value("CLF_PATH"):
                self.clf = Persistence._load_clf(self.settings["CLF_PATH"])

            self.satellite_type = self.get_value("SATELLITE_TYPE")
            self.working_dir = self.get_value("WORKING_DIR")
            self.file_extension = self.get_value("FILE_EXTENSION")
            self.hotspot_rf_path = self.get_value("HOTSPOT_RF_PATH")
            self.floating_rf_path = self.get_value("FLOATING_RF_PATH")

            if self.get_value("MORPHOLOGY_MATRIX_SIZE"):
                self.morphology_matrix_size = int(self.get_value("MORPHOLOGY_MATRIX_SIZE"))

            if self.get_value("MORPHOLOGY_ITERATIONS"):
                self.morphology_iterations = int(self.get_value("MORPHOLOGY_ITERATIONS"))

            if self.get_value("WASHED_UP_HEATMAP_SECTIONS"):
                self.washed_up_heatmap_sections = int(self.get_value("WASHED_UP_HEATMAP_SECTIONS"))

            if self.get_value("HEATMAP_HIGH_PROB"):
                self.heatmap_high_prob = int(self.get_value("HEATMAP_HIGH_PROB"))

            if self.get_value("HEATMAP_MEDIUM_PROB"):
                self.heatmap_medium_prob = int(self.get_value("HEATMAP_MEDIUM_PROB"))

            if self.get_value("HEATMAP_LOW_PROB"):
                self.heatmap_low_prob = int(self.get_value("HEATMAP_LOW_PROB"))

            self.hotspot_classified_postfix = self.get_value("HOTSPOT_CLASSIFIED_POSTFIX")
            self.hotspot_heatmap_postfix = self.get_value("HOTSPOT_HEATMAP_POSTFIX")
            self.floating_classified_postfix = self.get_value("FLOATING_CLASSIFIED_POSTFIX")
            self.floating_heatmap_postfix = self.get_value("FLOATING_HEATMAP_POSTFIX")
            self.floating_masked_classified_postfix = self.get_value("FLOATING_MASKED_CLASSIFIED_POSTFIX")
            self.floating_masked_heatmap_postfix = self.get_value("FLOATING_MASKED_HEATMAP_POSTFIX")
            self.washed_up_before_postfix = self.get_value("WASHED_UP_BEFORE_POSTFIX")
            self.washed_up_after_postfix = self.get_value("WASHED_UP_AFTER_POSTFIX")

            if self.get_value("TRAINING_LABEL_BLUE"):
                self.training_label_blue = int(self.get_value("TRAINING_LABEL_BLUE"))

            if self.get_value("TRAINING_LABEL_GREEN"):
                self.training_label_green = int(self.get_value("TRAINING_LABEL_GREEN"))

            if self.get_value("TRAINING_LABEL_RED"):
                self.training_label_red = int(self.get_value("TRAINING_LABEL_RED"))

            if self.get_value("TRAINING_LABEL_NIR"):
                self.training_label_nir = int(self.get_value("TRAINING_LABEL_NIR"))

            if self.get_value("TRAINING_LABEL_PI"):
                self.training_label_pi = int(self.get_value("TRAINING_LABEL_PI"))

            if self.get_value("TRAINING_LABEL_NDWI"):
                self.training_label_ndwi = int(self.get_value("TRAINING_LABEL_NDWI"))

            if self.get_value("TRAINING_LABEL_NDVI"):
                self.training_label_ndvi = int(self.get_value("TRAINING_LABEL_NDVI"))

            if self.get_value("TRAINING_LABEL_RNDVI"):
                self.training_label_rndvi = int(self.get_value("TRAINING_LABEL_RNDVI"))

            if self.get_value("TRAINING_LABEL_SR"):
                self.training_label_sr = int(self.get_value("TRAINING_LABEL_SR"))

            if self.get_value("TRAINING_ESTIMATORS"):
                self.training_estimators = int(self.get_value("TRAINING_ESTIMATORS"))

            if self.get_value("GARBAGE_MC_ID"):
                self.garbage_mc_id = int(self.get_value("GARBAGE_MC_ID"))

            if self.get_value("WATER_MC_ID"):
                self.water_mc_id = int(self.get_value("WATER_MC_ID"))

            if self.get_value("PLANET_BLUE_BAND"):
                self.planet_blue_band = int(self.get_value("PLANET_BLUE_BAND"))

            if self.get_value("PLANET_GREEN_BAND"):
                self.planet_green_band = int(self.get_value("PLANET_GREEN_BAND"))

            if self.get_value("PLANET_RED_BAND"):
                self.planet_red_band = int(self.get_value("PLANET_RED_BAND"))

            if self.get_value("PLANET_NIR_BAND"):
                self.planet_nir_band = int(self.get_value("PLANET_NIR_BAND"))

            if self.get_value("SENTINEL_BLUE_BAND"):
                self.sentinel_blue_band = int(self.get_value("SENTINEL_BLUE_BAND"))

            if self.get_value("SENTINEL_GREEN_BAND"):
                self.sentinel_green_band = int(self.get_value("SENTINEL_GREEN_BAND"))

            if self.get_value("SENTINEL_RED_BAND"):
                self.sentinel_red_band = int(self.get_value("SENTINEL_RED_BAND"))

            if self.get_value("SENTINEL_NIR_BAND"):
                self.sentinel_nir_band = int(self.get_value("SENTINEL_NIR_BAND"))

            self.colors = list()
            for i in range(16):
                index = "COLOR_" + str(i)
                if self.get_value(index):
                    self.colors.append(self._settings[index])
        except Exception:
            raise PersistenceLoadException()

    def save_constants(self) -> None:
        """
        Saves the values of the data members to the config file.

        :return: None
        """

        self._settings["SATELLITE_TYPE"] = self.satellite_type
        self._settings["WORKING_DIR"] = self.working_dir
        self._settings["FILE_EXTENSION"] = self.file_extension
        self._settings["HOTSPOT_RF_PATH"] = self.hotspot_rf_path
        self._settings["FLOATING_RF_PATH"] = self.floating_rf_path
        self._settings["MORPHOLOGY_MATRIX_SIZE"] = self.morphology_matrix_size
        self._settings["MORPHOLOGY_ITERATIONS"] = self.morphology_iterations
        self._settings["WASHED_UP_HEATMAP_SECTIONS"] = self.washed_up_heatmap_sections
        self._settings["HEATMAP_HIGH_PROB"] = self.heatmap_high_prob
        self._settings["HEATMAP_MEDIUM_PROB"] = self.heatmap_medium_prob
        self._settings["HEATMAP_LOW_PROB"] = self.heatmap_low_prob
        self._settings["HOTSPOT_CLASSIFIED_POSTFIX"] = self.hotspot_classified_postfix
        self._settings["HOTSPOT_HEATMAP_POSTFIX"] = self.hotspot_heatmap_postfix
        self._settings["FLOATING_CLASSIFIED_POSTFIX"] = self.floating_classified_postfix
        self._settings["FLOATING_HEATMAP_POSTFIX"] = self.floating_heatmap_postfix
        self._settings["FLOATING_MASKED_CLASSIFIED_POSTFIX"] = self.floating_masked_classified_postfix
        self._settings["FLOATING_MASKED_HEATMAP_POSTFIX"] = self.floating_masked_heatmap_postfix
        self._settings["WASHED_UP_BEFORE_POSTFIX"] = self.washed_up_before_postfix
        self._settings["WASHED_UP_AFTER_POSTFIX"] = self.washed_up_after_postfix
        self._settings["TRAINING_LABEL_BLUE"] = self.training_label_blue
        self._settings["TRAINING_LABEL_GREEN"] = self.training_label_green
        self._settings["TRAINING_LABEL_RED"] = self.training_label_red
        self._settings["TRAINING_LABEL_NIR"] = self.training_label_nir
        self._settings["TRAINING_LABEL_PI"] = self.training_label_pi
        self._settings["TRAINING_LABEL_NDWI"] = self.training_label_ndwi
        self._settings["TRAINING_LABEL_NDVI"] = self.training_label_ndvi
        self._settings["TRAINING_LABEL_RNDVI"] = self.training_label_rndvi
        self._settings["TRAINING_LABEL_SR"] = self.training_label_sr
        self._settings["TRAINING_ESTIMATORS"] = self.training_estimators
        self._settings["GARBAGE_MC_ID"] = self.garbage_mc_id
        self._settings["WATER_MC_ID"] = self.water_mc_id
        self._settings["PLANET_BLUE_BAND"] = self.planet_blue_band
        self._settings["PLANET_GREEN_BAND"] = self.planet_green_band
        self._settings["PLANET_RED_BAND"] = self.planet_red_band
        self._settings["PLANET_NIR_BAND"] = self.planet_nir_band
        self._settings["SENTINEL_BLUE_BAND"] = self.sentinel_blue_band
        self._settings["SENTINEL_GREEN_BAND"] = self.sentinel_green_band
        self._settings["SENTINEL_RED_BAND"] = self.sentinel_red_band
        self._settings["SENTINEL_NIR_BAND"] = self.sentinel_nir_band

        self._settings = {str(key): str(value) for key, value in self._settings.items()}

        for i in range(16):
            index = "COLOR_" + str(i)
            self._settings[index] = str(self.colors[i])

        try:
            Persistence._save_settings(self._settings, self._config_file)
        except Exception:
            raise

    def get_value(self, key: str) -> Union[str, None]:
        if key in self.settings.keys():
            return self.settings[key]
        else:
            return None

    # Static protected methods
    @staticmethod
    def _load_settings(path: str) -> Dict[str, str]:
        """
        Loads the given .json file into a Dictionary.

        :param path: path of the .json file
        :return: the loaded Dictionary
        """

        name, extension = os.path.splitext(path)

        if extension != ".json":
            raise JsonFileExtensionException(extension, path)

        try:
            with open(path, "r") as config_file:
                variables = json.load(config_file)
                return variables
        except Exception:
            raise

    @staticmethod
    def _save_settings(save_dict: Dict[str, str], path: str) -> None:
        """
        Saves the given Dictionary to the given file.

        :param save_dict: the Dictionary to be saved
        :param path: oath of the output file
        :return: None
        """

        name, extension = os.path.splitext(path)

        if extension != ".json":
            raise JsonFileExtensionException(extension, path)

        try:
            with open(path, "w") as file:
                json.dump(save_dict, file, indent=4)
        except Exception:
            raise

    @staticmethod
    def _load_data_file(path: str) -> Dict:
        """
        Loads the data file (GeoJSON) that contains the AOIs for later use.

        :return: the loaded data file in Dict form
        """

        with open(path, "r") as file:
            geojson_file = geojson.load(file)
        return geojson_file

    @staticmethod
    def _load_clf(path: str) -> RandomForestClassifier:
        """
        Loads the classifier for later use.

        :return: the loaded classifier
        """

        with open(path, "rb") as file:
            clf = pickle.load(file)
        return clf
