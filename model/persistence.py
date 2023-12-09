import os
import json
import pickle
import geojson
import jsonmerge


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
        """
        Sets class attributes dynamically based on the key-value pairs in the config file.
        A config.sample.json file must be specified, its values can be overwritten in a config.local.json file.
        """

        if not os.path.exists(self.config_file_path):
            raise ValueError(f"{self.config_file_path} does not exist!")

        with open(self.config_file_path, "r") as file:
            settings = json.load(file)

        config_local_path = os.path.join(os.path.dirname(self.config_file_path), "config.local.json")
        if os.path.exists(config_local_path):
            with open(config_local_path, "r") as file:
                config_local = json.load(file)
            settings = jsonmerge.merge(settings, config_local)

        for key, value in settings.items():
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
