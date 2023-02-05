import os
import json
import pickle
import geojson
import jsonmerge

from model.exceptions import *
from typing import Dict, Tuple
from collections import namedtuple


class Persistence(object):
    """
    A class that is the Persistence layer of the application. Its purpose is to load and save data.

    """

    def __init__(self, config_file_path: str) -> None:
        """
        The constructor of the Persistence class.

        """

        self.config_file_path = config_file_path
        self.clf = None
        self.data_file = None

        self.load()

    # Non-static public methods
    def load(self) -> None:
        name, extension = os.path.splitext(self.config_file_path)
        if extension != ".json":
            raise JsonFileExtensionException(extension, self.config_file_path)

        with open(self.config_file_path, "r") as file:
            settings = json.load(file, object_hook=Persistence._config_decoder)
            for key, value in settings._asdict().items():
                setattr(self, key, value)

        if hasattr(self, "data_file_path"):
            with open(self.data_file_path, "r") as file:
                self.data_file = geojson.load(file)

        if hasattr(self, "clf_path"):
            with open(self.clf_path, "rb") as file:
                self.clf = pickle.load(file)

    def save(self) -> None:
        """
        Saves the values of the data members to the config file.

        :return: None
        """

        settings = dict(self.__dict__)
        del settings["config_file_path"]

        with open(self.config_file_path, "r") as file:
            stored_config = json.load(file)

        new_config = jsonmerge.merge(stored_config, settings)

        with open(self.config_file_path, "w") as file:
            json.dump(new_config, file, indent=4)

    # Static protected methods
    @staticmethod
    def _config_decoder(config: Dict) -> Tuple:
        return namedtuple("settings", config.keys())(*config.values())
