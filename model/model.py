import os
import pickle
import geojson
import rasterio
import cv2 as cv
import numpy as np
import pandas as pd

from math import ceil
from osgeo import gdal
from model.exceptions import *
from matplotlib import cm
from PIL import ImageColor
from itertools import compress
from shapely.geometry import Point
from model.persistence import Persistence
from shapely.geometry.polygon import Polygon
from matplotlib.colors import ListedColormap
from sklearn.ensemble import RandomForestClassifier
from typing import List, Tuple, Callable, Union, TextIO, Dict

import traceback


# Constants for model.py
MAX_CLASS_COUNT = 15
MAX_CLASS_VALUE_COUNT = 10000000
LOW_PROB_VALUE = 1
MEDIUM_PROB_VALUE = 2
HIGH_PROB_VALUE = 3
HEATMAP_COLORS = {
    0: "#000000",
    1: "#1fff00",
    2: "#fff300",
    3: "#ff0000"
}


class Model(object):
    """
    A class that contains the program logic for this application.
    """

    def __init__(self, persistence: Persistence) -> None:
        """
        The constructor of the Model class.

        """

        super(Model, self).__init__()

        self._hotspot_rf = None
        self._floating_rf = None

        self._initialize_data_members()

        self._persistence = persistence

    # Class properties
    @property
    def result_files_hotspot(self) -> List[Tuple[str, str]]:
        return list(self._result_files_hotspot)

    @property
    def result_files_floating(self) -> List[Tuple[str, str]]:
        return list(self._result_files_floating)

    @property
    def result_files_washed_up(self) -> List[Tuple[str, str]]:
        return list(self._result_files_washed_up)

    @property
    def tag_ids(self) -> Dict:
        return self._tag_ids

    @property
    def tag_id_coords(self) -> Dict:
        return self._tag_id_coords

    @property
    def persistence(self) -> Persistence:
        return self._persistence

    @property
    def classification_mode(self) -> str:
        return self._classification_mode

    @property
    def classification_layer_data(self) -> Dict:
        return self._classification_layer_data 

    # Non-static public methods
    def load_random_forests(self) -> None:
        """
        Tries to load the Random Forest classifiers.

        :return: None
        :raise HotspotRandomForestFileException: if Random Forest file is incorrect for Hot-spot detection method
        :raise FloatingRandomForestFileException: if Random Forest file is incorrect for Floating waste detection method
        """

        try:
            with open(self._persistence.settings["HOTSPOT_RF_PATH"], "rb") as file:
                self._hotspot_rf = pickle.load(file)
        except Exception:
            self._hotspot_rf = None
            raise HotspotRandomForestFileException()

        try:
            with open(self._persistence.settings["FLOATING_RF_PATH"], "rb") as file:
                self._floating_rf = pickle.load(file)
        except Exception:
            self._floating_rf = None
            raise FloatingRandomForestFileException()

    def add_files(self, files: List[str], callback: Callable[[str], None]) -> None:
        """
        Adds new file path to Model, and notifies Controller if new file should be added to View.

        :param files: list of file paths opened by user
        :param callback: function in Controller, adds new item to View's opened files listbox
        :return: None
        """

        for file in files:
            if not (file in self._opened_files):
                self._opened_files.append(file)
                callback(file)

    def delete_files(self, files: List[str]) -> None:
        """
        Removes given file paths from Model.

        :param files: list of file paths to be removed
        :return: None
        """

        for file in files:
            if file in self._opened_files:
                self._opened_files.remove(file)

    def processing(self, process_id: int) -> Tuple[bool, bool]:
        """
        Starts the processing procedure.

        :param process_id: the id of the process to be started
        :return: all successful or not
        :raise RandomForestFileException: if there are no Random Forest model loaded
        """

        if (self._hotspot_rf is None) or (self._floating_rf is None):
            self.load_random_forests()

        if process_id == 1:
            if self._hotspot_rf is None:
                raise RandomForestFileException("Hot-spot")
            return self._process_hotspot_floating(hotspot=True)
        elif process_id == 2:
            if self._floating_rf is None:
                raise RandomForestFileException("Floating waste")
            return self._process_hotspot_floating(hotspot=False)
        elif process_id == 3:
            return self._process_washed_up()

    def save_training_input_file(self, path: str) -> None:
        """
        Saves given input file to training dictionary.

        :param path: path of the training file
        :return: None
        """

        self._tag_ids[path] = dict()

    def save_point_on_canvas(self, tag_id: int) -> None:
        """
        Saves the coordinates and tag id of a point on the canvas.

        :param tag_id: tag id of the point
        :return: None
        """

        self._point_tag_ids.append(tag_id)

    def toggle_classification_mode(self) -> None:
        if self._classification_mode == "polygon":
            self._classification_mode = "freehand"
        elif self._classification_mode == "freehand":
            self._classification_mode = "polygon"

    def add_classification_layer(self, image_name: str, layer: np.ndarray) -> None:
        """
        Adds a new classification layer

        :param image_name: the name of the image
        :param layer: the array representing the classification layer
        """
        self._classification_layer_data[image_name] = layer

    def get_classification_layer_data(self, image_name) -> np.ndarray:
        """
        Gets the classification layer data of the requested image

        :param image_name: the name of the image
        :return: The array containing the classification data of the image
        """
        return self._classification_layer_data[image_name]

    def set_classification_pixel_of_layer(self, image_name: str, coordinates: Tuple[int, int], mc_id: int) -> None:
        """
        sets a classification pixel of the given layer

        :param layer: the name of the image
        :param coordinates: the coordinates where the id will be placed
        :param mc_id: the id that will be placed at the given coordinates
        """
        mc_id_mul = mc_id * 100
        self._classification_layer_data[image_name][coordinates]= mc_id_mul

    def delete_classification_data(self, image_name: str) -> None:
        self._classification_layer_data.pop(image_name)

    def save_new_mc(self, training_file: str, mc_id: int, mc_name: str, mc_color: str) -> None:
        """
        Saves a new training class with the given file name, id, name and color.

        :param training_file: path of the training file that contains the training class to be saved
        :param mc_id: unique id of the training class
        :param mc_name: name of the training class
        :param mc_color: color of the training class
        :return: None
        """

        if training_file in self._tag_ids.keys():
            self._tag_ids[training_file][mc_id] = [mc_name, mc_color, []]

    def delete_mc(self, training_file: str, mc_id: int) -> List[int]:
        """
        Deletes a whole training class with all of its polygons.

        :param training_file: path of the training file that contains the Class to be deleted
        :param mc_id: unique id of the training class to be deleted
        :return: list of tag ids to be deleted
        """

        tag_ids = list()
        if training_file in self._tag_ids.keys():
            if mc_id in self._tag_ids[training_file].keys():
                tag_ids += self._tag_ids[training_file][mc_id][2]
                del self._tag_ids[training_file][mc_id]
        return tag_ids

    def delete_tag_id(self, training_file: str, tag_id: int) -> None:
        """
        Deletes the given tag id.

        :param training_file: path of the training file that contains the tag id to be deleted
        :param tag_id: tag id of the shape to be deleted
        :return: None
        """

        if training_file in self._tag_ids.keys():
            for mc_id in self._tag_ids[training_file].keys():
                if tag_id in self._tag_ids[training_file][mc_id][2]:
                    self._tag_ids[training_file][mc_id][2].remove(tag_id)
                    return

    def save_tag_id(self, training_file: str, mc_id: int, mc_name: str, color: str, tag_id: int) -> None:
        """
        Saves the tag id of a new shape in the training class.

        :param training_file: path of the training file
        :param mc_id: unique id of the training class
        :param mc_name: name of the training class
        :param color: color of the training class
        :param tag_id: tag id of a shape to be saved to the training class
        :return: None
        """

        if mc_id not in self._tag_ids[training_file].keys():
            self._tag_ids[training_file][mc_id] = [mc_name, color, []]

        self._tag_ids[training_file][mc_id][2].append(tag_id)

    def save_tag_id_coords(self, training_file: str, mc_id: int, mc_name: str,
                           coords: List[List[float]], bbox_coords: List[Tuple[int, ...]]) -> None:
        """
        Saves the coordinates of polygons and their bounding boxes of the specified training class.

        :param training_file: path of the training file
        :param mc_id: unique id of the training class
        :param mc_name: name of the training class
        :param coords: the list of coordinates of all polygons in the training class
        :param bbox_coords: the list of coordinates of all the bounding boxes in the training class
        :return: None
        """

        if training_file not in self._tag_id_coords.keys():
            self._tag_id_coords[training_file] = dict()

        self._tag_id_coords[training_file][mc_id] = [mc_name, coords, bbox_coords]

    def delete_points(self) -> List[int]:
        """
        Clears the lists of actual points on canvas. Returns the deleted tag ids.

        :return: list of tag ids deleted
        """

        point_tag_ids = list(self._point_tag_ids)
        self._point_tag_ids.clear()
        return point_tag_ids

    def place_polygon_on_canvas(self) -> List[int]:
        """
        Clears the lists containing the data of the next polygon to be placed.

        :return: list of coordinates of the vertices of the polygon
        """

        if len(self._point_tag_ids) >= 3:
            tag_ids = list(self._point_tag_ids)
            self._point_tag_ids.clear()
        else:
            tag_ids = list()

        return tag_ids

    def create_usable_training_data(self) -> Tuple[Dict[str, Dict], bool]:
        """
        Filters out the unusable data from self stored training data Dictionary.

        :return: Dictionary containing only the usable data and a bool value
        containing whether there is enough training data or not
        """

        usable_training_data = dict()

        tag_id_coords = self._tag_id_coords
        enough_data = list()
        for (training_file, mc_data) in tag_id_coords.items():
            enough_data.append(list(mc_data.keys()))
            for (mc_id, polygon_data) in mc_data.items():
                mc_name, coords, bbox_coords = polygon_data
                if coords:
                    if training_file not in usable_training_data.keys():
                        usable_training_data[training_file] = dict()
                    usable_training_data[training_file][mc_id] = polygon_data

        for labeled_layer in self._classification_layer_data.values():
                enough_data.append(labeled_layer[labeled_layer != 0] // 100)

        enough_data = np.unique(np.concatenate(enough_data))
        enough_data = len(enough_data) >= 2
        
        return usable_training_data, enough_data

    def add_polygon_values_to_image(self, training_file: str, usable_training_data: Dict[str, Dict]) -> np.ndarray:
        """
        Creates a numpy array that adds the polygons to the image layer.
        :param training_file: the training file that needs to be updated.
        :return a new image layer containing the updated data.
        """
        labeled_layer = self._classification_layer_data[training_file].copy()
        polygons = usable_training_data[training_file]
        for (mc_id, polygon_data) in polygons.items():
            mc_name, coords, bbox_coords = polygon_data
            for i in range(len(coords)):
                indices = Model._get_coords_inside_polygon(coords[i], bbox_coords[i])
                indices = np.asarray(indices).transpose()
                labeled_layer[indices[1], indices[0]] = mc_id * 100

        return labeled_layer

    def create_training_df(self, usable_training_data: Dict[str, Dict]) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
        """
        Creates a training DataFrame from the filtered training data.

        :param usable_training_data: filtered training data Dictionary
        :return: a DataFrame containing the training data for Random Forest classifier and a dictionary containing the labeling data for each image.
        """

        column_labels = ["SURFACE", "COD"]
        training_labels = self.get_training_labels()
        labels = Model._resolve_bands_indices_string(training_labels)
        labels = [value.upper() for value in labels]
        column_labels += labels
        labels = column_labels + labels
        file_dfs = []
        labeling_data = {}
        classified_layers = self._classification_layer_data

        for training_file, labeled_layer in classified_layers.items():
            bands_and_indices = self._get_bands_indices(self._persistence.settings["SATELLITE_TYPE"], training_file,
                                                        training_labels)
            bands_and_indices = np.asarray(bands_and_indices)
            if training_file in usable_training_data:
                labeled_layer = self.add_polygon_values_to_image(training_file, usable_training_data)

            classified_xs, classified_ys = np.nonzero(labeled_layer)
            classified_pixels = labeled_layer[classified_xs, classified_ys].flatten()
            list_of_columns = [
                np.full(fill_value = "", shape = classified_pixels.shape),
                classified_pixels.astype(int)
            ]
            classified_bands_and_indices = bands_and_indices[:, classified_xs, classified_ys]
            for i in range(classified_bands_and_indices.shape[0]):
                list_of_columns.append(classified_bands_and_indices[i])

            df = pd.DataFrame()
            df.index.name = "FID"
            for i in range(len(list_of_columns)):
                df[labels[i]] = list_of_columns[i]

            labeling_data[training_file] = labeled_layer
            file_dfs.append(df)

        training_df = pd.concat(file_dfs, ignore_index=True)
        training_df.index.name = "FID"

        return training_df, labeling_data

    def save_classification_images(self, labeled_images:Dict[str, np.ndarray]) -> None:
        """
        Saves the classification images with their metadata next to the image source. The classified image will have the "_classified" suffix associated with it.
        
        :param labeled_images: A dictionary containing the label data of each image.
        """
        for (image_path, image_data) in labeled_images.items():    
            mc_id_mc_name_pairs = {}
            for tag_data in self.tag_ids[image_path].items():
               mc_id, (mc_name, color, tags) = tag_data
               mc_id_mc_name_pairs[str(mc_id)] = mc_name

            stripped_path, extension = os.path.splitext(image_path)
            labeled_image_path = stripped_path + "_classified" + extension
            Model._save_tif(
                input_path=image_path, 
                array=[image_data], 
                shape=image_data.shape, 
                band_count=1,
                output_path=labeled_image_path,
                metadata=mc_id_mc_name_pairs)

    @staticmethod
    def estimate_garbage_area(
            input_path: str, image_type: str, garbage_c_id: int,
            low_medium_high: Tuple[bool, bool, bool] = None, pixel_sizes: Tuple[int, int] = None) -> Union[float, None]:
        """
        Estimates the area covered by garbage, based on the pixel size of a picture.

        :param input_path: input path of classified picture
        :param image_type: classified or heatmap
        :param garbage_c_id: Class ID of Garbage Class
        :param low_medium_high: boolean values based on the selected checkboxes in View
        :param pixel_sizes: size of a pixel in the image
        :return: estimated area if it can be calculated, None otherwise
        :raise NotEnoughBandsException: if the image to be opened does not have only one band
        :raise CodValueNotPresentException: if the Garbage Class is not present on the image
        :raise InvalidClassifiedImageException: if not all values could be divided by 100 on the classified image
        """

        try:
            dataset = gdal.Open(input_path, gdal.GA_ReadOnly)
            if dataset.RasterCount != 1:
                raise NotEnoughBandsException(dataset.RasterCount, 1, input_path)

            band = dataset.GetRasterBand(1)
            band = band.ReadAsArray()

            if not pixel_sizes:
                gt = dataset.GetGeoTransform()
                pixel_size_x = gt[1]
                pixel_size_y = -gt[5]
            else:
                pixel_size_x, pixel_size_y = pixel_sizes

            unique_values = np.unique(band)

            rows, cols = band.shape
            area = 0.0

            if image_type.lower() == "classified":
                if garbage_c_id * 100 not in unique_values:
                    raise CodValueNotPresentException("garbage", garbage_c_id * 100, input_path)

                cond_list = [value % 100 == 0 for value in unique_values]

                if not all(cond_list):
                    raise InvalidClassifiedImageException(input_path)

                for i in range(rows):
                    for j in range(cols):
                        if band[i, j] == garbage_c_id * 100:
                            area += pixel_size_x * pixel_size_y
            elif image_type.lower() == "heatmap":
                for i in range(rows):
                    for j in range(cols):
                        if (low_medium_high[0] and band[i, j] == LOW_PROB_VALUE) or \
                                (low_medium_high[1] and band[i, j] == MEDIUM_PROB_VALUE) or \
                                (low_medium_high[2] and band[i, j] == HIGH_PROB_VALUE):
                            area += pixel_size_x * pixel_size_y

            return area
        except NotEnoughBandsException:
            raise
        except CodValueNotPresentException:
            raise
        except InvalidClassifiedImageException:
            raise
        except Exception:
            return None
        finally:
            del dataset

    def create_and_save_random_forest(self, training_data_path: str, output_path: str) -> None:
        """
        Trains and saves a Random Forest classifier.

        :param training_data_path: path of training .csv file
        :param output_path: path of the trained Random Forest
        :return: None
        """

        training_labels = self.get_training_labels()
        labels = Model._resolve_bands_indices_string(training_labels)
        labels = [value.upper() for value in labels]

        clf = Model._create_random_forest(training_data_path, labels, ["COD"], int(self._persistence.settings["TRAINING_ESTIMATORS"]))

        pickle.dump(clf, open(output_path, "wb"))

    def get_training_labels(self) -> str:
        """
        Gets the checked training labels in SettingsView.

        :return: training label names separated by "-"
        """

        labels = list()
        if self._persistence.settings["TRAINING_LABEL_BLUE"] == "1":
            labels.append("blue")
        if self._persistence.settings["TRAINING_LABEL_GREEN"] == "1":
            labels.append("green")
        if self._persistence.settings["TRAINING_LABEL_RED"] == "1":
            labels.append("red")
        if self._persistence.settings["TRAINING_LABEL_NIR"] == "1":
            labels.append("nir")
        if self._persistence.settings["TRAINING_LABEL_PI"] == "1":
            labels.append("pi")
        if self._persistence.settings["TRAINING_LABEL_NDWI"] == "1":
            labels.append("ndwi")
        if self._persistence.settings["TRAINING_LABEL_NDVI"] == "1":
            labels.append("ndvi")
        if self._persistence.settings["TRAINING_LABEL_RNDVI"] == "1":
            labels.append("rndvi")
        if self._persistence.settings["TRAINING_LABEL_SR"] == "1":
            labels.append("sr")
        if self._persistence.settings["TRAINING_LABEL_APWI"] == "1":
            labels.append("apwi")
        return "-".join(labels)

    def get_classification_color_map(self, input_path: str, transparent_background: bool = False) -> ListedColormap:
        """
        Creates a color map based on the values in the classified image.

        :param input_path: path of the classified image
        :param transparent_background: whether the black background should be considered transparent
        :return: color map
        """

        with rasterio.open(input_path, "r") as dataset:
            input_array = dataset.read(1)

            unique_values = np.unique(input_array)
            cond_list = all([val % 100 == 0 for val in unique_values])

            if not cond_list:
                return cm.get_cmap("viridis")

            color_list = list()
            for value in unique_values:
                mc_id = int(value / 100)

                if mc_id >= len(self._persistence.colors):
                    continue

                color = self._persistence.colors[mc_id]
                rgba = ImageColor.getcolor(color, "RGBA")
                rgba = [val / 255 for val in rgba]

                if transparent_background and mc_id == 0:
                    rgba[-1] = 0

                color_list.append(rgba)

            if not color_list:
                return cm.get_cmap("viridis")

            color_map = ListedColormap(color_list)
            return color_map

    def get_classification_color_map_from_layer(self, input_array: np.ndarray, transparent_background: bool = False) -> ListedColormap:
        """
        Creates a color map based on the values in the classified image.

        :param input_array: the array of the classified image
        :param transparent_background: whether the black background should be considered transparent
        :return: color map
        """

        unique_values = np.unique(input_array)
        cond_list = all([val % 100 == 0 for val in unique_values])

        if not cond_list:
            return cm.get_cmap("viridis")

        color_list = list()
        for value in unique_values:
            mc_id = int(value / 100)

            if mc_id >= len(self._persistence.colors):
                continue

            color = self._persistence.colors[mc_id]
            rgba = ImageColor.getcolor(color, "RGBA")
            rgba = [val / 255 for val in rgba]

            if transparent_background and mc_id == 0:
                rgba[-1] = 0

            color_list.append(rgba)

        if not color_list:
            return cm.get_cmap("viridis")

        color_map = ListedColormap(color_list)
        return color_map

    # Non-static protected methods
    def _initialize_data_members(self) -> None:
        """
        Initializes the data members.

        :return: None
        """

        self._opened_files = list()
        self._result_files_hotspot = list()
        self._result_files_floating = list()
        self._result_files_washed_up = list()
        self._point_tag_ids = list()
        self._tag_ids = dict()
        self._tag_id_coords = dict()
        self._classification_mode = "polygon"
        self._classification_layer_data = dict()

    def _process_hotspot_floating(self, hotspot: bool) -> Tuple[bool, bool]:
        """
        Creates the output images of both the Hotspot and Floating waste detection processes.

        :param hotspot: True means Hot-spot detection, False means Floating waste detection
        :return: process successful or not
        """

        training_labels = self.get_training_labels()

        were_wrong_labels = False
        were_wrong_pictures = False

        for file in self._opened_files:
            if not os.path.exists(file):
                were_wrong_pictures = True
                continue
            tmp_file = self._save_bands_indices(
                satellite_type=self._persistence.settings["SATELLITE_TYPE"],
                input_path=file,
                save=training_labels,
                working_dir=self._persistence.settings["WORKING_DIR"],
                postfix="_",
                file_extension=self._persistence.settings["FILE_EXTENSION"],
            )

            low = int(self._persistence.settings["HEATMAP_LOW_PROB"]) / 100
            medium = int(self._persistence.settings["HEATMAP_MEDIUM_PROB"]) / 100
            high = int(self._persistence.settings["HEATMAP_HIGH_PROB"]) / 100
            clf = self._hotspot_rf if hotspot else self._floating_rf

            classification, heatmap = Model.create_classification_and_heatmap_with_random_forest(
                input_path=tmp_file,
                clf=clf,
                low_medium_high_values=(low, medium, high),
                garbage_c_id=int(self._persistence.settings["GARBAGE_MC_ID"]) * 100,
                working_dir=self._persistence.settings["WORKING_DIR"],
                classification_postfix=self._persistence.settings["HOTSPOT_CLASSIFIED_POSTFIX"],
                heatmap_postfix=self._persistence.settings["HOTSPOT_HEATMAP_POSTFIX"],
                file_extension=self._persistence.settings["FILE_EXTENSION"]
            )

            if classification and heatmap:
                if hotspot:
                    if not ((file, classification, heatmap) in self._result_files_hotspot):
                        self._result_files_hotspot.append((file, classification, heatmap))
                else:
                    masked_classification, masked_heatmap = Model.create_masked_classification_and_heatmap(
                        original_input_path=tmp_file,
                        classification_path=classification,
                        heatmap_path=heatmap,
                        garbage_c_id=int(self._persistence.settings["GARBAGE_MC_ID"]) * 100,
                        water_c_id=int(self._persistence.settings["WATER_MC_ID"]) * 100,
                        matrix=(int(self._persistence.settings["MORPHOLOGY_MATRIX_SIZE"]), int(self._persistence.settings["MORPHOLOGY_MATRIX_SIZE"])),
                        iterations=int(self._persistence.settings["MORPHOLOGY_ITERATIONS"]),
                        working_dir=self._persistence.settings["WORKING_DIR"],
                        classification_postfix=self._persistence.settings["FLOATING_MASKED_CLASSIFIED_POSTFIX"],
                        heatmap_postfix=self._persistence.settings["FLOATING_MASKED_HEATMAP_POSTFIX"],
                        file_extension=self._persistence.settings["FILE_EXTENSION"]
                    )

                    if not ((file, masked_classification, masked_heatmap) in self._result_files_floating):
                        self._result_files_floating.append((file, masked_classification, masked_heatmap))
            else:
                were_wrong_labels = True

            if os.path.exists(tmp_file):
                os.remove(tmp_file)

        return were_wrong_labels, were_wrong_pictures

    def _process_washed_up(self) -> Tuple[bool, bool]:
        """
        Creates the output images of the Washed up waste detection method.

        :return: process successful or not
        """

        were_wrong_labels = False
        were_wrong_pictures = False

        for i in range(len(self._opened_files)):
            for j in range(i + 1, len(self._opened_files)):
                file_1 = self._opened_files[i]
                file_2 = self._opened_files[j]

                if not os.path.exists(file_1) or not os.path.exists(file_2):
                    were_wrong_pictures = True
                    continue

                difference, coords_information = self._get_pi_difference(self._persistence.settings["SATELLITE_TYPE"],
                                                                         file_1, file_2)

                if not (difference is None) and not (coords_information is None):
                    before, after = self._get_pi_difference_heatmap(difference)

                    before_path = Model._output_path([file_1, file_2],
                                                     self._persistence.settings["WORKING_DIR"],
                                                     "_" + self._persistence.settings["WASHED_UP_BEFORE_POSTFIX"],
                                                     self._persistence.settings["FILE_EXTENSION"])
                    after_path = Model._output_path([file_1, file_2],
                                                    self._persistence.settings["WORKING_DIR"],
                                                    "_" + self._persistence.settings["WASHED_UP_AFTER_POSTFIX"],
                                                    self._persistence.settings["FILE_EXTENSION"])

                    Model._save_tif(
                        input_path=file_1,
                        array=[before],
                        shape=before.shape,
                        band_count=1,
                        output_path=before_path,
                        new_geo_trans=coords_information[0]
                    )

                    Model._save_tif(
                        input_path=file_2,
                        array=[after],
                        shape=after.shape,
                        band_count=1,
                        output_path=after_path,
                        new_geo_trans=coords_information[0]
                    )

                    if not ((file_1, file_2, before_path, after_path) in self._result_files_washed_up):
                        self._result_files_washed_up.append((file_1, file_2, before_path, after_path))
                else:
                    were_wrong_labels = True

        return were_wrong_labels, were_wrong_pictures

    @staticmethod
    def _get_satellite_band(settings_file: Dict, satellite_type: str, band: str) -> int:
        """
        Returns the given satellite's band index.

        :param settings_file: a dictionary containing the settings
        :param satellite_type: Name of the satellite, Sentinel-2 or Planet
        :param band: Name of satellite band
        :return: index of given satellite band
        :raise NameError: if wrong satellite name is given
        """

        satellite_name = satellite_type.upper().split("-")[0]
        band_name = band.upper()

        index = satellite_name + "_" + band_name + "_BAND"

        if index in settings_file.keys():
            return int(settings_file[index])
        else:
            raise NameError("Wrong satellite or band name!")

    def _get_bands_indices(self, satellite_type: str, input_path: str, get: str) -> List[np.ndarray]:
        """
        Returns a list of arrays, containing the band values and/or calculated index values.

        :param satellite_type: the type of the satellite that took the images
        :param input_path: path of the input image
        :param get: name of band/indices
        :return: band values and/or index values
        """

        get_list = Model._resolve_bands_indices_string(get)

        with rasterio.open(input_path, "r") as img:
            # read bands
            try:
                blue_ind = Model._get_satellite_band(self._persistence.settings, satellite_type, "Blue")
                green_ind = Model._get_satellite_band(self._persistence.settings, satellite_type, "Green")
                red_ind = Model._get_satellite_band(self._persistence.settings, satellite_type, "Red")
                nir_ind = Model._get_satellite_band(self._persistence.settings, satellite_type, "NIR")

                blue = (img.read(blue_ind)).astype(dtype="float32")
                green = (img.read(green_ind)).astype(dtype="float32")
                red = (img.read(red_ind)).astype(dtype="float32")
                nir = (img.read(nir_ind)).astype(dtype="float32")
            except Exception as exc:
                raise NotEnoughBandsException(img.count, max([blue_ind, green_ind, red_ind, nir_ind]), input_path) from None

            return Model._calculate_indices(get_list, {"blue": blue, "green": green, "red": red, "nir": nir})

    def _save_bands_indices(
            self, satellite_type: str, input_path: str, save: str,
            working_dir: str, postfix: str, file_extension: str) -> str:
        """
        Saves the specified band values and/or index values to a single- or multi-band tif file.

        :param satellite_type: the type of the satellite that took the images
        :param input_path: path of the input image
        :param save: name of band/indices
        :param working_dir: path of the working directory
        :param postfix: file name postfix of the output image
        :param file_extension: file extension of the output image
        :return: path of the output image
        """

        list_of_bands_and_indices = self._get_bands_indices(
            satellite_type=satellite_type,
            input_path=input_path,
            get=save,
        )

        bands = len(list_of_bands_and_indices)
        output_path = Model._output_path([input_path], working_dir, postfix, file_extension)

        Model._save_tif(
            input_path=input_path,
            array=list_of_bands_and_indices,
            shape=list_of_bands_and_indices[0].shape,
            band_count=bands,
            output_path=output_path,
        )

        return output_path

    def _get_pi_difference(self, satellite_type: str, input_path_1: str,
                           input_path_2: str) -> Union[Tuple[np.ndarray, Tuple], Tuple[None, None]]:
        """
        Calculates the PI difference of two different shaped images.

        :param satellite_type: the type of the satellite that took the images
        :param input_path_1: path of the first input image
        :param input_path_2: path of the second input image
        :return: matrix containing the difference values, coordinate information for later use
        """

        intersection_matrix, coords_information = Model._get_empty_intersection_matrix_and_start_coords(
                                                                                            input_path_1, input_path_2)

        if not (intersection_matrix is None) and not (coords_information is None):
            start_coords, input_1_start, input_2_start = coords_information

            [input_1_pi] = self._get_bands_indices(satellite_type, input_path_1, "pi")
            [input_2_pi] = self._get_bands_indices(satellite_type, input_path_2, "pi")

            img_1_size = input_1_pi.shape[0] * input_1_pi.shape[1]
            img_2_size = input_2_pi.shape[0] * input_2_pi.shape[1]

            rows, cols = intersection_matrix.shape

            for i in range(rows):
                for j in range(cols):
                    row_1, col_1 = input_1_start[0] + i, input_1_start[1] + j
                    row_2, col_2 = input_2_start[0] + i, input_2_start[1] + j
                    if img_1_size >= img_2_size:
                        intersection_matrix[i, j] = input_1_pi[row_1, col_1] - input_2_pi[row_2, col_2]
                    else:
                        intersection_matrix[i, j] = input_1_pi[row_2, col_2] - input_2_pi[row_1, col_1]

            return intersection_matrix, coords_information

        return None, None

    def _get_pi_difference_heatmap(self, difference_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Creates heatmaps for Washed up waste detection method.

        :param difference_matrix: matrix containing the PI difference of two images
        :return: before and after heatmap
        """

        heatmap_pos = np.zeros(
            shape=difference_matrix.shape,
            dtype=int
        )

        heatmap_neg = np.zeros(
            shape=difference_matrix.shape,
            dtype=int
        )

        unique_values = np.unique(difference_matrix)
        if (len(unique_values) == 1 and 0 in unique_values)\
                or (len(unique_values) == 1 and float("NaN") in unique_values)\
                or (len(unique_values) == 2 and 0 in unique_values and float("NaN") in unique_values):
            return heatmap_pos, heatmap_neg

        if not np.all(np.isnan(difference_matrix)):
            mean = np.nanmedian(difference_matrix)

            mean_difference_pos = np.empty_like(difference_matrix)
            mean_difference_neg = np.empty_like(difference_matrix)

            rows, cols = difference_matrix.shape

            for i in range(rows):
                for j in range(cols):
                    if difference_matrix[i, j] > mean:
                        mean_difference_pos[i, j] = difference_matrix[i, j] - mean
                        mean_difference_neg[i, j] = 0
                    else:
                        mean_difference_neg[i, j] = mean - difference_matrix[i, j]
                        mean_difference_pos[i, j] = 0

            max_pos = np.nanmax(mean_difference_pos)
            max_neg = np.nanmax(mean_difference_neg)

            for i in range(rows):
                for j in range(cols):
                    N_EQUAL_PARTS = int(self._persistence.settings["WASHED_UP_HEATMAP_SECTIONS"])

                    value_pos = mean_difference_pos[i, j]
                    equal_part_pos = max_pos / N_EQUAL_PARTS
                    if value_pos >= equal_part_pos * (N_EQUAL_PARTS - 1):
                        heatmap_pos[i, j] = HIGH_PROB_VALUE
                    elif equal_part_pos * (N_EQUAL_PARTS - 2) <= value_pos < equal_part_pos * (N_EQUAL_PARTS - 1):
                        heatmap_pos[i, j] = MEDIUM_PROB_VALUE
                    elif equal_part_pos * (N_EQUAL_PARTS - 3) <= value_pos < equal_part_pos * (N_EQUAL_PARTS - 2):
                        heatmap_pos[i, j] = LOW_PROB_VALUE

                    value_neg = mean_difference_neg[i, j]
                    equal_part_neg = max_neg / N_EQUAL_PARTS
                    if value_neg >= equal_part_neg * (N_EQUAL_PARTS - 1):
                        heatmap_neg[i, j] = HIGH_PROB_VALUE
                    elif equal_part_neg * (N_EQUAL_PARTS - 2) <= value_neg < equal_part_neg * (N_EQUAL_PARTS - 1):
                        heatmap_neg[i, j] = MEDIUM_PROB_VALUE
                    elif equal_part_neg * (N_EQUAL_PARTS - 3) <= value_neg < equal_part_neg * (N_EQUAL_PARTS - 2):
                        heatmap_neg[i, j] = LOW_PROB_VALUE

        return heatmap_pos, heatmap_neg

   
    # Static public methods
    @staticmethod
    def create_garbage_bbox_geojson(input_path: str, file: TextIO, searched_value: List[int]) -> None:
        """
        Creates the GeoJSON file containing the bounding boxes of garbage areas.

        :param input_path: classified image or heatmap image
        :param file: the GeoJSON file
        :param searched_value: the wanted value
        :return: None
        """

        bbox_coords = Model._get_bbox_coordinates_of_same_areas(input_path, searched_value)

        if bbox_coords is not None:
            features = list()

            polygon_id = 1
            for bbox in bbox_coords:
                bbox.append(bbox[0])
                polygon = geojson.Polygon([bbox])
                features.append(geojson.Feature(geometry=polygon, properties={"id": str(polygon_id)}))
                polygon_id += 1

            feature_collection = geojson.FeatureCollection(features)

            geojson.dump(feature_collection, file, indent=4)

    @staticmethod
    def create_masked_classification_and_heatmap(
            original_input_path: str, classification_path: str, heatmap_path: str,
            garbage_c_id: int, water_c_id: int, matrix: Tuple[int, int],
            iterations: int, working_dir: str, classification_postfix: str,
            heatmap_postfix: str, file_extension: str) -> Tuple[str, str]:
        """
        Creates the masked classification and masked heatmap based on the input classification and input heatmap.
        Uses morphological transformations (opening and dilation).

        :param original_input_path: path of the original image
        :param classification_path: path of the classified image
        :param heatmap_path: path of the heatmap image
        :param garbage_c_id: the COD value of the "GARBAGE" class
        :param water_c_id: the COD value of the "WATER" class
        :param matrix: the shape of the matrix in the opening transformation
        :param iterations: the number of iterations in the dilation transformation
        :param working_dir: the path of the working directory
        :param classification_postfix: the file name postfix of the masked and classified image
        :param heatmap_postfix: the file name postfix of the masked heatmap image
        :param file_extension: the file extension of the output images
        :return: the paths of the output images
        """

        # open inputs
        with rasterio.open(classification_path, "r") as classification_matrix, \
             rasterio.open(heatmap_path, "r") as heatmap_matrix:

            # create matrices
            classification_matrix = classification_matrix.read(1)
            heatmap_matrix = heatmap_matrix.read(1)
            morphology_matrix = np.empty_like(classification_matrix)
            masked_classification = np.empty_like(classification_matrix)
            masked_heatmap = np.empty_like(classification_matrix)

            rows, cols = classification_matrix.shape

            # output paths
            morphology_path = Model._output_path([original_input_path], working_dir, "morphology", file_extension)
            opening_path = Model._output_path([original_input_path], working_dir, "morphology_opening", file_extension)
            dilation_path = Model._output_path([original_input_path], working_dir, "morphology_opening_dilation",
                                               file_extension)
            masked_classification_path = Model._output_path([original_input_path], working_dir, classification_postfix,
                                                            file_extension)
            masked_heatmap_path = Model._output_path([original_input_path], working_dir, heatmap_postfix,
                                                     file_extension)

            for i in range(rows):
                for j in range(cols):
                    if classification_matrix[i, j] == garbage_c_id or classification_matrix[i, j] == water_c_id:
                        morphology_matrix[i, j] = 1
                    else:
                        morphology_matrix[i, j] = 0

            Model._save_tif(
                input_path=original_input_path,
                array=[morphology_matrix],
                shape=morphology_matrix.shape,
                band_count=1,
                output_path=morphology_path,
            )

            opening = Model._morphology("opening", morphology_path, opening_path, matrix=matrix)

            if opening is not None:
                dilation = Model._morphology("dilation", opening_path, dilation_path, iterations=iterations)

                if dilation is not None:
                    for i in range(rows):
                        for j in range(cols):
                            if dilation[i, j] == 1:
                                masked_classification[i, j] = classification_matrix[i, j]
                                masked_heatmap[i, j] = heatmap_matrix[i, j]
                            else:
                                masked_classification[i, j] = 0
                                masked_heatmap[i, j] = 0

                    Model._save_tif(
                        input_path=original_input_path,
                        array=[masked_classification],
                        shape=masked_classification.shape,
                        band_count=1,
                        output_path=masked_classification_path,
                    )

                    Model._save_tif(
                        input_path=original_input_path,
                        array=[masked_heatmap],
                        shape=masked_heatmap.shape,
                        band_count=1,
                        output_path=masked_heatmap_path,
                    )

            if os.path.exists(morphology_path):
                os.remove(morphology_path)
            if os.path.exists(opening_path):
                os.remove(opening_path)
            if os.path.exists(dilation_path):
                os.remove(dilation_path)

            return masked_classification_path, masked_heatmap_path

    @staticmethod
    def get_heatmap_color_map(input_path: str, low_medium_high: List[str]) -> ListedColormap:
        """
        Creates a color map based on the values in the heatmap image.

        :param input_path: path of the heatmap image
        :param low_medium_high: which Checkboxes are selected in View
        :return: color map
        """

        with rasterio.open(input_path, "r") as dataset:
            input_array = dataset.read(1)

            unique_values = np.unique(input_array)
            cond_list = all([val in HEATMAP_COLORS.keys() for val in unique_values])

            if not cond_list:
                return cm.get_cmap("viridis")

            color_list = list()
            for value in unique_values:
                if (value == 1 and "low" in low_medium_high) or \
                   (value == 2 and "medium" in low_medium_high) or \
                   (value == 3 and "high" in low_medium_high):
                    color = HEATMAP_COLORS[value]
                else:
                    color = HEATMAP_COLORS[0]
                rgba = ImageColor.getcolor(color, "RGBA")
                rgba = [val / 255 for val in rgba]
                color_list.append(rgba)

            if not color_list:
                return cm.get_cmap("viridis")

            color_map = ListedColormap(color_list)
            return color_map

    # Static protected methods
    @staticmethod
    def _create_random_forest(
            training_data_path: str, column_names: List[str], label_names: List[str],
            estimators: int) -> RandomForestClassifier:
        """
        Trains the RandomForestClassifier based on the training data.

        :param training_data_path: path of the .csv file containing the training data
        :param column_names: training labels
        :param label_names: classification labels
        :param estimators: number of decision trees in the Forest
        :return: the trained RandomForestClassifier
        """

        # read training data
        df = pd.read_csv(training_data_path, sep=';')
        
        #narrow training data
        data = df[column_names]
        label = df[label_names]
        label = np.ravel(label).astype(str)

        # make classification
        clf = RandomForestClassifier(n_estimators=estimators, n_jobs=-1)
        clf.fit(data, label)

        # return random forest for later use
        return clf

    @staticmethod
    def _calculate_indices(get_list: List[str], bands: Dict[str, np.ndarray]) -> List[np.ndarray]:
            # calculate indices
            # PI = NIR / (NIR + RED)
            # NDWI = (GREEN - NIR) / (GREEN + NIR)
            # NDVI = (NIR - RED) / (NIR + RED)
            # RNDVI = (RED - NIR) / (RED + NIR)
            # SR = NIR / RED
            blue = bands["blue"]
            green = bands["green"]
            red = bands["red"]
            nir = bands["nir"]

            list_of_bands_and_indices = list()
            for item in get_list:
                if item == "blue":
                    list_of_bands_and_indices.append(blue)
                elif item == "green":
                    list_of_bands_and_indices.append(green)
                elif item == "red":
                    list_of_bands_and_indices.append(red)
                elif item == "nir":
                    list_of_bands_and_indices.append(nir)
                elif item == "pi":
                    pi = Model._calculate_index(numerator=nir, denominator=nir + red)
                    list_of_bands_and_indices.append(pi)
                elif item == "ndwi":
                    ndwi = Model._calculate_index(numerator=green - nir, denominator=green + nir)
                    list_of_bands_and_indices.append(ndwi)
                elif item == "ndvi":
                    ndvi = Model._calculate_index(numerator=nir - red, denominator=nir + red)
                    list_of_bands_and_indices.append(ndvi)
                elif item == "rndvi":
                    rndvi = Model._calculate_index(numerator=red - nir, denominator=red + nir)
                    list_of_bands_and_indices.append(rndvi)
                elif item == "sr":
                    sr = Model._calculate_index(numerator=nir, denominator=red)
                    list_of_bands_and_indices.append(sr)
            return list_of_bands_and_indices
    
    @staticmethod
    def _make_noisy_data(data: pd.DataFrame) -> pd.DataFrame:
        """
        Adds noise to given dataframe
        :param data: the dataframe to add noise to
        :return: A dataframe that has noisy data added to it.
        """

        data_copy = data.copy()[["BLUE", "GREEN", "RED", "NIR", "PI", "NDWI", "NDVI", "RNDVI", "SR"]]
        noise = (np.random.normal(0, .1, data_copy.shape) * 1000).astype(int)
        data_copy = data_copy + noise
        bands = {
            "blue": np.expand_dims(data_copy["BLUE"].to_numpy(), axis=0),
            "green": np.expand_dims(data_copy["GREEN"].to_numpy(), axis = 0),
            "red": np.expand_dims(data_copy["RED"].to_numpy(), axis = 0),
            "nir": np.expand_dims(data_copy["NIR"].to_numpy(), axis = 0)
        }

        requested_indices = [col.lower() for col in data_copy.columns]
        labels = [data["SURFACE"].to_numpy(),data["COD"].to_numpy()]
        indices = [id.flatten() for id in Model._calculate_indices(requested_indices, bands)]
        labels_indices = [pd.Series(col) for col in labels + indices]

        data_noisy = pd.DataFrame(labels_indices).T
        data_noisy.columns = data.columns
        data_noisy.index.name = "FID"
        
        return data_noisy
            

    @staticmethod
    def _get_coords_inside_polygon(polygon_coords: List[float], bbox_coords: Tuple[int, ...]) -> List[Tuple[int, int]]:
        """
        Calculates the coordinates inside a given polygon.

        :param polygon_coords: the coordinates of the vertices of a polygon
        :param bbox_coords: the coordinates of vertices of the bounding box containing the polygon
        :return: the list of (x, y) coordinates inside the polygon
        """

        polygon_coords = list(map(int, polygon_coords))
        polygon_coords = zip(polygon_coords[0::2], polygon_coords[1::2])
        polygon = Polygon(polygon_coords)

        bbox_coords = list(map(int, bbox_coords))
        coords = list()

        for y in range(bbox_coords[1], bbox_coords[3] + 1):
            for x in range(bbox_coords[0], bbox_coords[2] + 1):
                p = Point(x, y)
                if polygon.contains(p):
                    coords.append((x, y))

        return coords

    @staticmethod
    def _output_path(input_paths: List[str], working_dir: str, postfix: str, output_file_extension: str) -> str:
        """
        Returns generated output path from given parameters.

        :param input_paths: list of input file paths
        :param working_dir: path to working directory
        :param postfix: postfix of output file
        :param output_file_extension: file extension of output file
        :return: generated output path
        """

        if working_dir == "":
            filename, file_extension = os.path.splitext(input_paths[0])
            output_path = filename + "_" + postfix + "." + output_file_extension
        else:
            file_names = list()
            for path in input_paths:
                file_name = "".join(path.split(".")[:-1]).split("/")[-1]
                file_names.append(file_name)
                output_path = working_dir + "/" + "_".join(file_names) + postfix + "." + output_file_extension
        return output_path

    @staticmethod
    def _save_tif(
            input_path: str, array: List[np.ndarray], shape: Tuple[int, int],
            band_count: int, output_path: str, new_geo_trans: Tuple[float, float] = None,
            metadata: Dict[str, str] = None) -> None:
        """
        Saves arrays (1 or more) to a georeferenced tif file.

        :param input_path: georeferenced input image
        :param array: list of arrays to be saved
        :param shape: shape of the output image
        :param band_count: number of bands in the output tif file
        :param output_path: path of the output image
        :param new_geo_trans: other GeoTransform if it is needed
        :param metadata: metadata that can be added to the file if needed
        :return: None
        """

        try:
            img_gdal = gdal.Open(input_path, gdal.GA_ReadOnly)
            x_pixels = shape[1]
            y_pixels = shape[0]

            driver = gdal.GetDriverByName("GTiff")
            geotrans = img_gdal.GetGeoTransform()
            projection = img_gdal.GetProjection()

            if not (new_geo_trans is None):
                geotrans = list(geotrans)
                geotrans[0] = new_geo_trans[0]
                geotrans[3] = new_geo_trans[1]
                geotrans = tuple(geotrans)

            dataset = driver.Create(output_path, x_pixels, y_pixels, band_count, gdal.GDT_Float32)
            dataset.SetGeoTransform(geotrans)
            dataset.SetProjection(projection)
            
            if not (metadata is None):
                dataset.SetMetadata(metadata)

            for band in range(band_count):
                outband = dataset.GetRasterBand(band + 1)
                outband.WriteArray(array[band][:, :])
                outband.SetNoDataValue(float("NaN"))
                outband.FlushCache()

            dataset.FlushCache()
        finally:
            del img_gdal

    @staticmethod
    def _calculate_index(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
        """
        Calculating an index based on given numerator and denominator.

        :param numerator: numerator matrix
        :param denominator: denominator matrix
        :return: result matrix, containing the calculated values
        """

        # variables
        rows = numerator.shape[0]
        cols = numerator.shape[1]
        index = np.ndarray(
            shape=numerator.shape,
            dtype="float32",
        )

        numerator_nanmin = np.nanmin(numerator)
        numerator_nanmax = np.nanmax(numerator)        

        # calculate index
        nan_mask = np.isnan(numerator) | np.isnan(denominator)
        numerator_zero_mask = numerator == 0
        denominator_zero_mask = denominator == 0

        invalid_mask = nan_mask | (numerator_zero_mask & denominator_zero_mask)
        valid_mask = np.logical_not(invalid_mask)

        valid_denominator_non_zero_mask = valid_mask & np.logical_not(denominator_zero_mask)
        valid_denominator_zero_mask = valid_mask & denominator_zero_mask

        numerator_positive_denumerator_zero_mask = valid_denominator_zero_mask & (numerator > 0)
        numerator_negative_denumerator_zero_mask = valid_denominator_zero_mask & (numerator < 0)

        index[invalid_mask] = float("NaN")
        index[numerator_positive_denumerator_zero_mask] = numerator_nanmax
        index[numerator_negative_denumerator_zero_mask] = numerator_nanmin
        index[valid_denominator_non_zero_mask] = numerator[valid_denominator_non_zero_mask] / denominator[valid_denominator_non_zero_mask]

        # return index values
        return index

    @staticmethod
    def _resolve_bands_indices_string(string: str) -> List[str]:
        """
        Resolves band strings.

        :param string: name of band/indices separated by "-", or "all", "all_no_blue", "bands", "indices"
        :return: list containing the band/index values
        """

        string_list = string.lower().split("-")

        if "all" in string_list:
            return ["blue", "green", "red", "nir", "pi", "ndwi", "ndvi", "rndvi", "sr", "apwi"]
        elif "all_no_blue" in string_list:
            return ["green", "red", "nir", "pi", "ndwi", "ndvi", "rndvi", "sr"]
        elif "bands" in string_list:
            return ["blue", "green", "red", "nir"]
        elif "indices" in string_list:
            return ["pi", "ndwi", "ndvi", "rndvi", "sr"]

        bands_indices = list()
        if "blue" in string_list:
            bands_indices.append("blue")
        if "green" in string_list:
            bands_indices.append("green")
        if "red" in string_list:
            bands_indices.append("red")
        if "nir" in string_list:
            bands_indices.append("nir")
        if "pi" in string_list:
            bands_indices.append("pi")
        if "ndwi" in string_list:
            bands_indices.append("ndwi")
        if "ndvi" in string_list:
            bands_indices.append("ndvi")
        if "rndvi" in string_list:
            bands_indices.append("rndvi")
        if "sr" in string_list:
            bands_indices.append("sr")
        if "apwi" in string_list:
            bands_indices.append("apwi")

        return bands_indices

    @staticmethod
    def _get_coords_of_pixel(i: int, j: int, gt: Tuple[int, ...]) -> Tuple[float, float]:
        """
        Calculates the geographical coordinate of the pixel in row "i" and column "j",
        based on the picture's GeoTransform.

        :param i: row index
        :param j: column index
        :param gt: GeoTransform of the picture
        :return: the calculated geographical coordinates: x and y
        """

        x_coord = gt[0] + j * gt[1] + i * gt[2]
        y_coord = gt[3] + j * gt[4] + i * gt[5]

        return x_coord, y_coord

    @staticmethod
    def _calculate_coords_for_pixels(input_path: str) -> Union[np.ndarray, None]:
        """
        Calculates geographical coordinates for each pixel on the input image.

        :param input_path: path of the input image
        :return: matrix containing the geographical coordinates
        """

        try:
            ds = gdal.Open(input_path, gdal.GA_ReadOnly)
            width = ds.RasterXSize
            height = ds.RasterYSize
            gt = ds.GetGeoTransform()

            coords_xy = np.ndarray(
                shape=(height, width),
                dtype="float32,float32",
            )

            for i in range(height):
                for j in range(width):
                    coords_xy[i, j] = Model._get_coords_of_pixel(i, j, gt)

            return coords_xy
        finally:
            del ds

    @staticmethod
    def _get_empty_intersection_matrix_and_start_coords(
            input_path_1: str, input_path_2: str) -> Union[Tuple[np.ndarray, Tuple], Tuple[None, None]]:
        """
        Calculates the intersection of two different sized matrices.

        :param input_path_1: path of the first input image
        :param input_path_2: path of the second input image
        :return: empty intersection matrix, coordinate information for later use
        """

        coords_1 = Model._calculate_coords_for_pixels(input_path_1)
        coords_2 = Model._calculate_coords_for_pixels(input_path_2)

        if (coords_1 is not None) and (coords_2 is not None):
            img_1_size = coords_1.shape[0] * coords_1.shape[1]
            img_2_size = coords_2.shape[0] * coords_2.shape[1]

            larger_img = coords_1 if img_1_size >= img_2_size else coords_2
            smaller_img = coords_1 if img_1_size < img_2_size else coords_2

            selector = np.in1d(larger_img.flatten(), smaller_img.flatten())
            intersection = list(compress(range(len(selector)), selector))

            new_rows, new_cols = 0, 0

            if intersection:
                larger_rows, larger_cols = np.unravel_index(intersection, larger_img.shape)
                larger_start_index = (larger_rows[0], larger_cols[0])

                start_coord = larger_img[larger_start_index]

                smaller_start_index = np.where(smaller_img == start_coord)
                smaller_start_index = smaller_start_index[0][0], smaller_start_index[1][0]

                i, j = larger_start_index
                k, l = smaller_start_index

                while i < larger_img.shape[0] and k < smaller_img.shape[0]:
                    new_rows += 1
                    i += 1
                    k += 1

                while j < larger_img.shape[1] and l < smaller_img.shape[1]:
                    new_cols += 1
                    j += 1
                    l += 1

                intersection_matrix = np.ndarray(
                    shape=(new_rows, new_cols),
                    dtype="float32",
                )

                coords_information = (start_coord, larger_start_index, smaller_start_index)

                return intersection_matrix, coords_information

        return None, None

    @staticmethod
    def create_classification_and_heatmap_with_random_forest(
            input_path: str, clf: RandomForestClassifier, low_medium_high_values: Tuple[float, ...],
            garbage_c_id: int, working_dir: str, classification_postfix: str,
            heatmap_postfix: str, file_extension: str) -> Tuple[str, str]:
        """
        Creates classification and garbage heatmap with Random Forest Classifier.

        :param input_path: input path of the image to be processed
        :param clf: an instance of RandomForestClassifier
        :param low_medium_high_values: probabilities
        :param garbage_c_id: Class ID of Garbage Class
        :param working_dir: path of the working directory
        :param classification_postfix: file name postfix of the classified image
        :param heatmap_postfix: file name postfix of the heatmap image
        :param file_extension: file extension of the output files
        :return: path of the classified image and the heatmap image
        """

        try:
            ds = gdal.Open(input_path, gdal.GA_ReadOnly)

            # initialize variables
            rows = ds.RasterYSize
            cols = ds.RasterXSize
            bands = ds.RasterCount
            array = ds.ReadAsArray().astype(dtype="float32")

            classes = clf.classes_

            classification = np.zeros(shape=rows * cols, dtype=int)
            heatmap = np.zeros(shape=rows * cols, dtype=int)

            # merge band values
            array = np.stack(array, axis=2)

            # reshape array
            array = np.reshape(array, [rows * cols, bands])

            # array to data frame
            array_df = pd.DataFrame(array, dtype='float32')

            split_size = ceil(array_df.shape[0] / ceil((array_df.shape[0] * MAX_CLASS_COUNT) / MAX_CLASS_VALUE_COUNT))
            split_count = ceil((array_df.shape[0] * MAX_CLASS_COUNT) / MAX_CLASS_VALUE_COUNT)
            for c in range(split_count):
                new_array_df = array_df[c * split_size:(c + 1) * split_size].dropna(axis="index")
                pred_proba = clf.predict_proba(new_array_df)

                counter = 0
                for i in range(c * split_size, (c + 1) * split_size):
                    if i == rows * cols:
                        break

                    if np.any(np.isnan(array[i])):
                        continue

                    max_ind = np.argmax(pred_proba[counter])
                    max_value = pred_proba[counter][max_ind]

                    if classes[max_ind] == garbage_c_id:
                        if max_value >= low_medium_high_values[2]:
                            heatmap[i] = HIGH_PROB_VALUE
                        elif low_medium_high_values[1] <= max_value < low_medium_high_values[2]:
                            heatmap[i] = MEDIUM_PROB_VALUE
                        elif low_medium_high_values[0] <= max_value < low_medium_high_values[1]:
                            heatmap[i] = LOW_PROB_VALUE

                    classification[i] = classes[max_ind]

                    counter += 1

            classification = classification.reshape((rows, cols))
            heatmap = heatmap.reshape((rows, cols))
            classification_output_path = Model._output_path([input_path], working_dir, classification_postfix, file_extension)
            heatmap_output_path = Model._output_path([input_path], working_dir, heatmap_postfix, file_extension)

            # save classification
            Model._save_tif(
                input_path=input_path,
                array=[classification],
                shape=classification.shape,
                band_count=1,
                output_path=classification_output_path,
            )

            # save heatmap
            Model._save_tif(
                input_path=input_path,
                array=[heatmap],
                shape=heatmap.shape,
                band_count=1,
                output_path=heatmap_output_path,
            )

            return classification_output_path, heatmap_output_path
        except Exception:
            traceback.print_exc()
            return "", ""
        finally:
            del ds

    @staticmethod
    def _morphology(morph_type: str, path: str, output: str,
                    matrix: Tuple[int, int] = (3, 3), iterations: int = 1) -> Union[np.ndarray, None]:
        """
        Morphological transformations: https://docs.opencv.org/4.5.2/d9/d61/tutorial_py_morphological_ops.html

        :param morph_type: type of the morphology: "erosion", "dilation", "opening", "closing"
        :param path: input path
        :param output: output path
        :param matrix: the helper matrix used for the algorithm
        :param iterations: number of iterations per image
        :return: matrix representing the result of transformation
        """

        try:
            img = cv.imread(path, 2)
            kernel = np.ones(matrix, np.uint8)

            operation = None

            if morph_type == "erosion":
                operation = cv.erode(img, kernel, iterations=iterations)
            elif morph_type == "dilation":
                operation = cv.dilate(img, kernel, iterations=iterations)
            elif morph_type == "opening":
                operation = cv.morphologyEx(img, cv.MORPH_OPEN, kernel)
            elif morph_type == "closing":
                operation = cv.morphologyEx(img, cv.MORPH_CLOSE, kernel)

            Model._save_tif(
                input_path=path,
                array=[operation],
                shape=operation.shape,
                band_count=1,
                output_path=output,
            )

            return operation
        except Exception:
            return None
        finally:
            del img

    @staticmethod
    def _valid_row(shape: Tuple[int, int], row: int) -> bool:
        """
        Decides whether the given row is inside the array with the given shape, or not.
        Source: https://playandlearntocode.com/article/flood-fill-algorithm-in-python

        :param shape: shape of the array
        :param row: index of the row
        :return: True or False
        """

        return 0 <= row < shape[0]

    @staticmethod
    def _valid_col(shape: Tuple[int, int], col: int) -> bool:
        """
        Decides whether the given column is inside the array with the given shape, or not.
        Source: https://playandlearntocode.com/article/flood-fill-algorithm-in-python

        :param shape: shape of the array
        :param col: index of the column
        :return: True or False
        """

        return 0 <= col < shape[1]

    @staticmethod
    def _is_search_value(matrix: np.ndarray, row: int, col: int, search_value: List[int]) -> bool:
        """
        Checks whether the value of the given pixel is the expected value or not.
        Source: https://playandlearntocode.com/article/flood-fill-algorithm-in-python

        :param matrix: an array of a classified image or a heatmap image
        :param row: row index
        :param col: column index
        :param search_value: the expected value
        :return: True or False
        """

        if not Model._valid_row(matrix.shape, row):
            return False

        if not Model._valid_col(matrix.shape, col):
            return False

        if matrix[row, col] in search_value:
            return True
        else:
            return False

    @staticmethod
    def _iterative_flood_fill(matrix: np.ndarray, row: int, col: int,
                              search_value: List[int]) -> Union[List[Tuple[int, int]], None]:
        """
        Iterative version of Flood fill algorithm.
        Returns the indices of a region containing the expected value.
        Source: https://playandlearntocode.com/article/flood-fill-algorithm-in-python

        :param matrix: an array of a classified image or a heatmap image
        :param row: row index
        :param col: column index
        :param search_value: the expected value
        :return: list of tuples containing the coordinates of pixels inside the region
        """

        if not Model._valid_row(matrix.shape, row):
            return

        if not Model._valid_col(matrix.shape, col):
            return

        if matrix[row, col] not in search_value:
            return

        q = list()  # init empty queue (FIFO)
        matrix[row, col] = -1  # mark as visited
        q.append([row, col])  # add to queue
        region = list()

        while len(q) > 0:
            [cur_row, cur_col] = q[0]
            region.append(tuple(q[0]))

            del q[0]

            if Model._is_search_value(matrix, cur_row - 1, cur_col, search_value):
                matrix[cur_row - 1, cur_col] = -1
                q.append([cur_row - 1, cur_col])

            if Model._is_search_value(matrix, cur_row + 1, cur_col, search_value):
                matrix[cur_row + 1, cur_col] = -1
                q.append([cur_row + 1, cur_col])

            if Model._is_search_value(matrix, cur_row, cur_col - 1, search_value):
                matrix[cur_row, cur_col - 1] = -1
                q.append([cur_row, cur_col - 1])

            if Model._is_search_value(matrix, cur_row, cur_col + 1, search_value):
                matrix[cur_row, cur_col + 1] = -1
                q.append([cur_row, cur_col + 1])

        return region

    @staticmethod
    def _find_regions(matrix: np.ndarray, search_value: List[int]) -> List[List[Tuple[int, int]]]:
        """
        Calculates all the separate regions containing the expected value.

        :param matrix: an array of a classified image or a heatmap image
        :param search_value: the expected value
        :return: list of all the regions
        """

        rows, cols = matrix.shape
        all_regions = list()

        for row in range(rows):
            for col in range(cols):
                if matrix[row, col] in search_value:
                    region = Model._iterative_flood_fill(matrix, row, col, search_value)
                    if not (region is None):
                        all_regions.append(region)

        return all_regions

    @staticmethod
    def _get_bbox_indices_of_region(region: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Calculates the indices of the bounding box of the given region.

        :param region: list containing the indices of region members
        :return: list of indices of the bounding box
        """

        row_indices = [i for (i, j) in region]
        col_indices = [j for (i, j) in region]

        min_row = min(row_indices)
        max_row = max(row_indices)
        min_col = min(col_indices)
        max_col = max(col_indices)

        bbox = [(min_row, min_col), (min_row, max_col), (max_row, max_col), (max_row, min_col)]

        return bbox

    @staticmethod
    def _get_bbox_indices_of_all_regions(all_regions: List[List[Tuple[int, int]]]) -> List[List[Tuple[int, int]]]:
        """
        Returns the indices of the bounding boxes of all the given regions.

        :param all_regions: list of regions
        :return: list containing the indices of bounding boxes of the regions
        """

        bboxes = list()

        for region in all_regions:
            bbox = Model._get_bbox_indices_of_region(region)
            bboxes.append(bbox)

        return bboxes

    @staticmethod
    def _get_bbox_coordinates_of_same_areas(input_path: str,
                                            search_value: List[int]) -> Union[List[List[Tuple[int, ...]]], None]:
        """
        Calculates the coordinates of bounding boxes of the same areas.

        :param input_path: path of a classified image or a heatmap image
        :param search_value: the wanted value
        :return: list of coordinates of bounding boxes of the same areas
        """

        try:
            dataset = gdal.Open(input_path, gdal.GA_ReadOnly)
            matrix = dataset.GetRasterBand(1)
            matrix = matrix.ReadAsArray()
            gt = dataset.GetGeoTransform()

            pixel_size_x = gt[1]
            pixel_size_y = -gt[5]

            regions = Model._find_regions(matrix, search_value)
            bboxes = Model._get_bbox_indices_of_all_regions(regions)
            bbox_coords = list()

            for bbox in bboxes:
                coords = list()

                upper_left = Model._get_coords_of_pixel(bbox[0][0], bbox[0][1], gt)
                upper_right = Model._get_coords_of_pixel(bbox[1][0], bbox[1][1], gt)
                bottom_right = Model._get_coords_of_pixel(bbox[2][0], bbox[2][1], gt)
                bottom_left = Model._get_coords_of_pixel(bbox[3][0], bbox[3][1], gt)

                coords.append(upper_left)
                coords.append((upper_right[0] + pixel_size_x, upper_right[1]))
                coords.append((bottom_right[0] + pixel_size_x, bottom_right[1] - pixel_size_y))
                coords.append((bottom_left[0], bottom_left[1] - pixel_size_y))

                bbox_coords.append(coords)

            return bbox_coords
        except Exception:
            return None
        finally:
            del dataset
