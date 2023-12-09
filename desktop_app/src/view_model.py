import os
import pickle
import rasterio
import numpy as np
import pandas as pd

from matplotlib import cm
from PIL import ImageColor
from model.model import Model
from model.exceptions import *
from model.persistence import Persistence
from matplotlib.colors import ListedColormap
from typing import List, Tuple, Callable, Dict
from sklearn.ensemble import RandomForestClassifier


HEATMAP_COLORS = {0: "#000000", 1: "#1fff00", 2: "#fff300", 3: "#ff0000"}


class ViewModel(Model):
    """
    It is derived from the main Model class and contains logic specifically for the desktop_app.

    """

    def __init__(self, persistence: Persistence) -> None:
        """
        Constructor of ViewModel.
        """

        super(ViewModel, self).__init__(persistence)

        self._classification_mode = None
        self._hotspot_rf = None
        self._floating_rf = None

        self._initialize_data_members()

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
    def classification_mode(self) -> str:
        return self._classification_mode

    @property
    def classification_layer_data(self) -> Dict:
        return self._classification_layer_data

    # Non-static public methods
    def get_training_labels(self) -> str:
        """
        Gets the checked training labels in SettingsView.

        :return: training label names separated by "-"
        """

        labels = list()
        if self.persistence.training_label_blue == 1:
            labels.append("blue")
        if self.persistence.training_label_green == 1:
            labels.append("green")
        if self.persistence.training_label_red == 1:
            labels.append("red")
        if self.persistence.training_label_nir == 1:
            labels.append("nir")
        if self.persistence.training_label_pi == 1:
            labels.append("pi")
        if self.persistence.training_label_ndwi == 1:
            labels.append("ndwi")
        if self.persistence.training_label_ndvi == 1:
            labels.append("ndvi")
        if self.persistence.training_label_rndvi == 1:
            labels.append("rndvi")
        if self.persistence.training_label_sr == 1:
            labels.append("sr")
        if self.persistence.training_label_apwi == 1:
            labels.append("apwi")
        return "-".join(labels)

    def load_random_forests(self) -> None:
        """
        Tries to load the Random Forest classifiers.

        :return: None
        :raise HotspotRandomForestFileException: if Random Forest file is incorrect for Hot-spot detection method
        :raise FloatingRandomForestFileException: if Random Forest file is incorrect for Floating waste detection method
        """

        try:
            with open(self.persistence.hotspot_rf_path, "rb") as file:
                self._hotspot_rf = pickle.load(file)
        except Exception:
            self._hotspot_rf = None
            raise HotspotRandomForestFileException()

        try:
            with open(self.persistence.floating_rf_path, "rb") as file:
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

    def set_classification_pixel_of_layer(self, image_name: str, coordinates: Tuple[int, int], c_id: int) -> None:
        """
        sets a classification pixel of the given layer

        :param image_name: the name of the image
        :param coordinates: the coordinates where the id will be placed
        :param c_id: the id that will be placed at the given coordinates
        """

        c_id_mul = c_id * 100
        self._classification_layer_data[image_name][coordinates] = c_id_mul

    def delete_classification_data(self, image_name: str) -> None:
        self._classification_layer_data.pop(image_name)

    def save_new_c(self, training_file: str, c_id: int, c_name: str, c_color: str) -> None:
        """
        Saves a new training class with the given file name, id, name and color.

        :param training_file: path of the training file that contains the training class to be saved
        :param c_id: unique id of the training class
        :param c_name: name of the training class
        :param c_color: color of the training class
        :return: None
        """

        if training_file in self._tag_ids.keys():
            self._tag_ids[training_file][c_id] = [c_name, c_color, []]

    def delete_c(self, training_file: str, c_id: int) -> List[int]:
        """
        Deletes a whole training class with all of its polygons.

        :param training_file: path of the training file that contains the Class to be deleted
        :param c_id: unique id of the training class to be deleted
        :return: list of tag ids to be deleted
        """

        tag_ids = list()
        if training_file in self._tag_ids.keys():
            if c_id in self._tag_ids[training_file].keys():
                tag_ids += self._tag_ids[training_file][c_id][2]
                del self._tag_ids[training_file][c_id]
        return tag_ids

    def delete_tag_id(self, training_file: str, tag_id: int) -> None:
        """
        Deletes the given tag id.

        :param training_file: path of the training file that contains the tag id to be deleted
        :param tag_id: tag id of the shape to be deleted
        :return: None
        """

        if training_file in self._tag_ids.keys():
            for c_id in self._tag_ids[training_file].keys():
                if tag_id in self._tag_ids[training_file][c_id][2]:
                    self._tag_ids[training_file][c_id][2].remove(tag_id)
                    return

    def save_tag_id(self, training_file: str, c_id: int, c_name: str, color: str, tag_id: int) -> None:
        """
        Saves the tag id of a new shape in the training class.

        :param training_file: path of the training file
        :param c_id: unique id of the training class
        :param c_name: name of the training class
        :param color: color of the training class
        :param tag_id: tag id of a shape to be saved to the training class
        :return: None
        """

        if c_id not in self._tag_ids[training_file].keys():
            self._tag_ids[training_file][c_id] = [c_name, color, []]

        self._tag_ids[training_file][c_id][2].append(tag_id)

    def save_tag_id_coords(
        self,
        training_file: str,
        c_id: int,
        c_name: str,
        coords: List[List[float]],
        bbox_coords: List[Tuple[int, ...]],
    ) -> None:
        """
        Saves the coordinates of polygons and their bounding boxes of the specified training class.

        :param training_file: path of the training file
        :param c_id: unique id of the training class
        :param c_name: name of the training class
        :param coords: the list of coordinates of all polygons in the training class
        :param bbox_coords: the list of coordinates of all the bounding boxes in the training class
        :return: None
        """

        if training_file not in self._tag_id_coords.keys():
            self._tag_id_coords[training_file] = dict()

        self._tag_id_coords[training_file][c_id] = [c_name, coords, bbox_coords]

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
        for training_file, c_data in tag_id_coords.items():
            usable_c_ids = []
            for c_id, polygon_data in c_data.items():
                c_name, coords, bbox_coords = polygon_data
                if coords:
                    if training_file not in usable_training_data.keys():
                        usable_training_data[training_file] = dict()
                    usable_training_data[training_file][c_id] = polygon_data
                    usable_c_ids.append(c_id)
            enough_data.append(usable_c_ids)

        for labeled_layer in self._classification_layer_data.values():
            enough_data.append(labeled_layer[labeled_layer != 0] // 100)

        enough_data = np.unique(np.concatenate(enough_data))
        enough_data = len(enough_data) >= 2

        return usable_training_data, enough_data

    def add_polygon_values_to_image(self, training_file: str, usable_training_data: Dict[str, Dict]) -> np.ndarray:
        """
        Creates a numpy array that adds the polygons to the image layer.
        :param training_file: the training file that needs to be updated.
        :param usable_training_data:
        :return a new image layer containing the updated data.
        """

        labeled_layer = self._classification_layer_data[training_file].copy()
        polygons = usable_training_data[training_file]
        for c_id, polygon_data in polygons.items():
            c_name, coords, bbox_coords = polygon_data
            for i in range(len(coords)):
                indices = Model.get_coords_inside_polygon(coords[i], bbox_coords[i])
                indices = np.asarray(indices).transpose()
                labeled_layer[indices[1], indices[0]] = c_id * 100

        return labeled_layer

    def create_training_df(self, usable_training_data: Dict[str, Dict]) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
        """
        Creates a training DataFrame from the filtered training data.

        :param usable_training_data: filtered training data Dictionary
        :return: a DataFrame containing the training data for Random Forest classifier
                 and a dictionary containing the labeling data for each image.
        """

        column_labels = ["SURFACE", "COD"]
        training_labels = self.get_training_labels()
        labels = Model.resolve_bands_indices_string(training_labels)
        labels = [value.upper() for value in labels]
        column_labels += labels
        labels = column_labels + labels
        file_dfs = []
        labeling_data = {}
        classified_layers = self._classification_layer_data

        for training_file, labeled_layer in classified_layers.items():
            bands_and_indices = self.get_bands_indices(training_file, training_labels)
            bands_and_indices = np.asarray(bands_and_indices)
            if training_file in usable_training_data:
                labeled_layer = self.add_polygon_values_to_image(training_file, usable_training_data)

            classified_xs, classified_ys = np.nonzero(labeled_layer)
            classified_pixels = labeled_layer[classified_xs, classified_ys].flatten()
            list_of_columns = [
                np.full(fill_value="", shape=classified_pixels.shape),
                classified_pixels.astype(int),
            ]
            classified_bands_and_indices = bands_and_indices[:, classified_xs, classified_ys]
            for i in range(classified_bands_and_indices.shape[0]):
                list_of_columns.append(classified_bands_and_indices[i])

            df = pd.DataFrame()
            for i in range(len(list_of_columns)):
                df[labels[i]] = list_of_columns[i]

            labeling_data[training_file] = labeled_layer
            file_dfs.append(df)

        training_df = pd.concat(file_dfs, ignore_index=True)
        training_df.index.name = "FID"

        return training_df, labeling_data

    def save_classification_images(self, labeled_images: Dict[str, np.ndarray]) -> None:
        """
        Saves the classification images with their metadata next to the image source.
        The classified image will have the "_classified" suffix associated with it.

        :param labeled_images: A dictionary containing the label data of each image.
        """

        for image_path, image_data in labeled_images.items():
            c_id_c_name_pairs = {}
            for tag_data in self.tag_ids[image_path].items():
                c_id, (c_name, color, tags) = tag_data
                c_id_c_name_pairs[str(c_id)] = c_name

            stripped_path, extension = os.path.splitext(image_path)
            labeled_image_path = stripped_path + "_classified" + extension
            Model.save_tif(
                input_path=image_path,
                array=[image_data],
                shape=image_data.shape,
                band_count=1,
                output_path=labeled_image_path,
                metadata=c_id_c_name_pairs,
            )

    def create_and_save_random_forest(self, training_data_path: str, output_path: str) -> None:
        """
        Trains and saves a Random Forest classifier.

        :param training_data_path: path of training .csv file
        :param output_path: path of the trained Random Forest
        :return: None
        """

        training_labels = self.get_training_labels()
        labels = Model.resolve_bands_indices_string(training_labels)
        labels = [value.upper() for value in labels]

        clf = self._create_random_forest(
            training_data_path,
            labels,
            ["COD"],
            self.persistence.training_estimators,
        )

        pickle.dump(clf, open(output_path, "wb"))

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
                c_id = int(value / 100)

                if c_id >= len(self.persistence.colors):
                    continue

                color = self.persistence.colors[c_id]
                rgba = ImageColor.getcolor(color, "RGBA")
                rgba = [val / 255 for val in rgba]

                if transparent_background and c_id == 0:
                    rgba[-1] = 0

                color_list.append(rgba)

            if not color_list:
                return cm.get_cmap("viridis")

            color_map = ListedColormap(color_list)
            return color_map

    def get_classification_color_map_from_layer(
        self, input_array: np.ndarray, transparent_background: bool = False
    ) -> ListedColormap:
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
            c_id = int(value / 100)

            if c_id >= len(self.persistence.colors):
                continue

            color = self.persistence.colors[c_id]
            rgba = ImageColor.getcolor(color, "RGBA")
            rgba = [val / 255 for val in rgba]

            if transparent_background and c_id == 0:
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
            tmp_file = self.save_bands_indices(
                input_path=file, save=training_labels, postfix=training_labels, working_dir=self.persistence.working_dir
            )

            clf = self._hotspot_rf if hotspot else self._floating_rf

            (
                classification,
                heatmap,
            ) = self.create_classification_and_heatmap_with_random_forest(
                input_path=tmp_file,
                clf=clf,
                classification_postfix=self.persistence.hotspot_classified_postfix,
                heatmap_postfix=self.persistence.hotspot_heatmap_postfix,
            )

            if classification and heatmap:
                if hotspot:
                    if not ((file, classification, heatmap) in self._result_files_hotspot):
                        self._result_files_hotspot.append((file, classification, heatmap))
                else:
                    (
                        masked_classification,
                        masked_heatmap,
                    ) = self.create_masked_classification_and_heatmap(
                        original_input_path=tmp_file,
                        classification_path=classification,
                        heatmap_path=heatmap,
                        classification_postfix=self.persistence.floating_masked_classified_postfix,
                        heatmap_postfix=self.persistence.floating_masked_heatmap_postfix,
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

                difference, coords_information = self.get_pi_difference(file_1, file_2)

                if not (difference is None) and not (coords_information is None):
                    before, after = self.get_pi_difference_heatmap(difference)

                    before_path = Model.output_path(
                        [file_1, file_2],
                        self.persistence.washed_up_before_postfix,
                        self.persistence.file_extension,
                        self.persistence.working_dir,
                    )
                    after_path = Model.output_path(
                        [file_1, file_2],
                        self.persistence.washed_up_after_postfix,
                        self.persistence.file_extension,
                        self.persistence.working_dir,
                    )

                    Model.save_tif(
                        input_path=file_1,
                        array=[before],
                        shape=before.shape,
                        band_count=1,
                        output_path=before_path,
                        new_geo_trans=coords_information[0],
                    )

                    Model.save_tif(
                        input_path=file_2,
                        array=[after],
                        shape=after.shape,
                        band_count=1,
                        output_path=after_path,
                        new_geo_trans=coords_information[0],
                    )

                    if not ((file_1, file_2, before_path, after_path) in self._result_files_washed_up):
                        self._result_files_washed_up.append((file_1, file_2, before_path, after_path))
                else:
                    were_wrong_labels = True

        return were_wrong_labels, were_wrong_pictures

    # Static public methods
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
                if (
                    (value == 1 and "low" in low_medium_high)
                    or (value == 2 and "medium" in low_medium_high)
                    or (value == 3 and "high" in low_medium_high)
                ):
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
        training_data_path: str,
        column_names: List[str],
        label_names: List[str],
        estimators: int,
    ) -> RandomForestClassifier:
        """
        Trains the RandomForestClassifier based on the training data.

        :param training_data_path: path of the .csv file containing the training data
        :param column_names: training labels
        :param label_names: classification labels
        :param estimators: number of decision trees in the Forest
        :return: the trained RandomForestClassifier
        """

        # read training data
        df = pd.read_csv(training_data_path, sep=";")

        # narrow training data
        data = df[column_names]
        label = df[label_names]
        label = np.ravel(label).astype(str)

        # make classification
        clf = RandomForestClassifier(n_estimators=estimators, n_jobs=-1)
        clf.fit(data, label)

        # return random forest for later use
        return clf
