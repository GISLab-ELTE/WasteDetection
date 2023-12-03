import os
import copy
import pickle
import pyproj
import geojson
import rasterio
import traceback
import cv2 as cv
import numpy as np
import pandas as pd
import geopandas as gpd

from shapely.geometry import shape
from shapely.ops import unary_union
from math import ceil
from osgeo import gdal, osr
from matplotlib import cm
from PIL import ImageColor
from itertools import compress
from model.exceptions import *
from shapely.geometry import Point
from model.persistence import Persistence
from shapely.geometry.polygon import Polygon
from matplotlib.colors import ListedColormap
from sklearn.ensemble import RandomForestClassifier
from typing import List, Tuple, Callable, Union, TextIO, Dict


class Model(object):
    """
    A class that contains the program logic for this application.
    """

    def __init__(self, persistence: Persistence) -> None:
        """
        The constructor of the Model class.

        """

        super(Model, self).__init__()

        self._persistence = persistence

        self.pixel_size_x = None
        self.pixel_size_y = None

        if self._persistence.satellite_type.lower() == "PlanetScope".lower():
            self.pixel_size_x = self.pixel_size_y = 3
        elif self._persistence.satellite_type.lower() == "Sentinel-2".lower():
            self.pixel_size_x = self.pixel_size_y = 10

    def estimate_garbage_area(
        self,
        input_path: str,
        image_type: str,
        prob: str = None,
    ) -> Union[float, None]:
        """
        Estimates the area covered by garbage, based on the pixel size of a picture.

        :param input_path: input path of classified picture
        :param image_type: classified or heatmap
        :return: estimated area if it can be calculated, None otherwise
        :raise NotEnoughBandsException: if the image to be opened does not have only one band
        :raise CodValueNotPresentException: if the Garbage Class is not present on the image
        :raise InvalidClassifiedImageException: if not all values could be divided by 100 on the classified image
        """

        if image_type == "heatmap" and not prob:
            raise ValueError("If image_type is heatmap then the value of prob must be given!")
        if prob and prob not in ["low", "medium", "high"]:
            raise ValueError("The value of prob must be low, medium, high!")

        try:
            dataset = gdal.Open(input_path, gdal.GA_ReadOnly)
            if dataset.RasterCount != 1:
                raise NotEnoughBandsException(dataset.RasterCount, 1, input_path)

            band = dataset.GetRasterBand(1)
            band = band.ReadAsArray()
            unique_values = np.unique(band)

            rows, cols = band.shape
            area = 0.0

            if image_type.lower() == "classified":
                if self._persistence.garbage_c_id * 100 not in unique_values:
                    return 0
                    # raise CodValueNotPresentException(
                    #     "garbage", garbage_c_id * 100, input_path
                    # )

                cond_list = [value % 100 == 0 for value in unique_values]

                if not all(cond_list):
                    return 0
                    # raise InvalidClassifiedImageException(input_path)

                for i in range(rows):
                    for j in range(cols):
                        if band[i, j] == self._persistence.garbage_c_id * 100:
                            area += self.pixel_size_x * self.pixel_size_y
            elif image_type.lower() == "heatmap":
                for i in range(rows):
                    for j in range(cols):
                        if (
                            prob == "low" and band[i, j] == self._persistence.low_prob_value
                            or prob == "medium" and band[i, j] == self._persistence.medium_prob_value
                            or prob == "high" and band[i, j] == self._persistence.high_prob_value
                        ):
                            area += self.pixel_size_x * self.pixel_size_y

            return area
        # except NotEnoughBandsException:
        #     raise
        # except CodValueNotPresentException:
        #     raise
        # except InvalidClassifiedImageException:
        #     raise
        except Exception:
            traceback.print_exc()
            return None
        finally:
            del dataset

    def get_satellite_band(self, band: str) -> int:
        """
        Returns the given satellite's band index.

        :param band: Name of satellite band.
        :return: Index of given satellite band.
        :raise NameError: If wrong satellite name is given.
        """

        satellite_name = self._persistence.satellite_type.lower()
        band_name = band.lower()

        index = satellite_name + "_" + band_name

        if hasattr(self._persistence, index):
            return getattr(self._persistence, index)
        else:
            raise NameError("Wrong satellite or band name!")

    def get_bands_indices(
        self, input_path: str, get: str
    ) -> List[np.ndarray]:
        """
        Returns a list of arrays, containing the band values and/or calculated index values.

        :param input_path: path of the input image
        :param get: name of band/indices
        :return: band values and/or index values
        """

        get_list = Model.resolve_bands_indices_string(get)

        with rasterio.open(input_path, "r") as img:
            # read bands
            try:
                blue_ind = self.get_satellite_band("Blue")
                green_ind = self.get_satellite_band("Green")
                red_ind = self.get_satellite_band("Red")
                nir_ind = self.get_satellite_band("NIR")

                blue = (img.read(blue_ind)).astype(dtype="float32")
                green = (img.read(green_ind)).astype(dtype="float32")
                red = (img.read(red_ind)).astype(dtype="float32")
                nir = (img.read(nir_ind)).astype(dtype="float32")
            except Exception as exc:
                raise NotEnoughBandsException(
                    img.count, max([blue_ind, green_ind, red_ind, nir_ind]), input_path
                ) from None

            return Model.calculate_indices(
                get_list, {"blue": blue, "green": green, "red": red, "nir": nir}
            )

    def save_bands_indices(
        self,
        input_path: str,
        save: str,
        postfix: str,
    ) -> str:
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

        list_of_bands_and_indices = self.get_bands_indices(
            input_path=input_path,
            get=save,
        )

        bands = len(list_of_bands_and_indices)
        output_path = Model.output_path(
            [input_path], postfix, self._persistence.file_extension, self._persistence.working_dir
        )

        Model.save_tif(
            input_path=input_path,
            array=list_of_bands_and_indices,
            shape=list_of_bands_and_indices[0].shape,
            band_count=bands,
            output_path=output_path,
        )

        return output_path

    def get_pi_difference(
        self, input_path_1: str, input_path_2: str
    ) -> Union[Tuple[np.ndarray, Tuple], Tuple[None, None]]:
        """
        Calculates the PI difference of two different shaped images.

        :param input_path_1: path of the first input image
        :param input_path_2: path of the second input image
        :return: matrix containing the difference values, coordinate information for later use
        """

        (
            intersection_matrix,
            coords_information,
        ) = Model.get_empty_intersection_matrix_and_start_coords(
            input_path_1, input_path_2
        )

        if not (intersection_matrix is None) and not (coords_information is None):
            start_coords, input_1_start, input_2_start = coords_information

            [input_1_pi] = self.get_bands_indices(input_path_1, "pi")
            [input_2_pi] = self.get_bands_indices(input_path_2, "pi")

            img_1_size = input_1_pi.shape[0] * input_1_pi.shape[1]
            img_2_size = input_2_pi.shape[0] * input_2_pi.shape[1]

            rows, cols = intersection_matrix.shape

            for i in range(rows):
                for j in range(cols):
                    row_1, col_1 = input_1_start[0] + i, input_1_start[1] + j
                    row_2, col_2 = input_2_start[0] + i, input_2_start[1] + j
                    if img_1_size >= img_2_size:
                        intersection_matrix[i, j] = (
                            input_1_pi[row_1, col_1] - input_2_pi[row_2, col_2]
                        )
                    else:
                        intersection_matrix[i, j] = (
                            input_1_pi[row_2, col_2] - input_2_pi[row_1, col_1]
                        )

            return intersection_matrix, coords_information

        return None, None

    def get_pi_difference_heatmap(
        self, difference_matrix: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Creates heatmaps for Washed up waste detection method.

        :param difference_matrix: matrix containing the PI difference of two images
        :return: before and after heatmap
        """

        heatmap_pos = np.zeros(shape=difference_matrix.shape, dtype=int)

        heatmap_neg = np.zeros(shape=difference_matrix.shape, dtype=int)

        unique_values = np.unique(difference_matrix)
        if (
            (len(unique_values) == 1 and 0 in unique_values)
            or (len(unique_values) == 1 and float("NaN") in unique_values)
            or (
                len(unique_values) == 2
                and 0 in unique_values
                and float("NaN") in unique_values
            )
        ):
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
                    n_equal_parts = int(self._persistence.washed_up_heatmap_sections)

                    value_pos = mean_difference_pos[i, j]
                    equal_part_pos = max_pos / n_equal_parts
                    if value_pos >= equal_part_pos * (n_equal_parts - 1):
                        heatmap_pos[i, j] = self._persistence.high_prob_value
                    elif (
                        equal_part_pos * (n_equal_parts - 2)
                        <= value_pos
                        < equal_part_pos * (n_equal_parts - 1)
                    ):
                        heatmap_pos[i, j] = self._persistence.medium_prob_value
                    elif (
                        equal_part_pos * (n_equal_parts - 3)
                        <= value_pos
                        < equal_part_pos * (n_equal_parts - 2)
                    ):
                        heatmap_pos[i, j] = self._persistence.low_prob_value

                    value_neg = mean_difference_neg[i, j]
                    equal_part_neg = max_neg / n_equal_parts
                    if value_neg >= equal_part_neg * (n_equal_parts - 1):
                        heatmap_neg[i, j] = self._persistence.high_prob_value
                    elif (
                        equal_part_neg * (n_equal_parts - 2)
                        <= value_neg
                        < equal_part_neg * (n_equal_parts - 1)
                    ):
                        heatmap_neg[i, j] = self._persistence.medium_prob_value
                    elif (
                        equal_part_neg * (n_equal_parts - 3)
                        <= value_neg
                        < equal_part_neg * (n_equal_parts - 2)
                    ):
                        heatmap_neg[i, j] = self._persistence.low_prob_value

        return heatmap_pos, heatmap_neg

    # Static public methods
    @staticmethod
    def create_garbage_bbox_geojson(
        input_path: str, file: TextIO, searched_value: List[int]
    ) -> None:
        """
        Creates the GeoJSON file containing the bounding boxes of garbage areas.

        :param input_path: classified image or heatmap image
        :param file: the GeoJSON file
        :param searched_value: the wanted value
        :return: None
        """

        bbox_coords = Model.get_bbox_coordinates_of_same_areas(
            input_path, searched_value
        )

        if bbox_coords is not None:
            features = list()

            polygon_id = 1
            for bbox in bbox_coords:
                bbox.append(bbox[0])
                polygon = geojson.Polygon([bbox])
                features.append(
                    geojson.Feature(
                        geometry=polygon, properties={"id": str(polygon_id)}
                    )
                )
                polygon_id += 1

            feature_collection = geojson.FeatureCollection(features)

            geojson.dump(feature_collection, file, indent=4)

    def create_masked_classification_and_heatmap(
        self,
        original_input_path: str,
        classification_path: str,
        heatmap_path: str,
        classification_postfix: str,
        heatmap_postfix: str,
    ) -> Tuple[str, str]:
        """
        Creates the masked classification and masked heatmap based on the input classification and input heatmap.
        Uses morphological transformations (opening and dilation).

        :param original_input_path: path of the original image
        :param classification_path: path of the classified image
        :param heatmap_path: path of the heatmap image
        :return: the paths of the output images
        """

        # open inputs
        with rasterio.open(
            classification_path, "r"
        ) as classification_matrix, rasterio.open(heatmap_path, "r") as heatmap_matrix:
            # create matrices
            classification_matrix = classification_matrix.read(1)
            heatmap_matrix = heatmap_matrix.read(1)
            morphology_matrix = np.empty_like(classification_matrix)
            masked_classification = np.empty_like(classification_matrix)
            masked_heatmap = np.empty_like(classification_matrix)

            rows, cols = classification_matrix.shape

            # output paths
            morphology_path = Model.output_path(
                [original_input_path], "morphology", self._persistence.file_extension, self._persistence.working_dir
            )
            opening_path = Model.output_path(
                [original_input_path], "morphology_opening", self._persistence.file_extension, self._persistence.working_dir,
            )
            dilation_path = Model.output_path(
                [original_input_path],
                "morphology_opening_dilation",
                self._persistence.file_extension,
                self._persistence.working_dir,
            )
            masked_classification_path = Model.output_path(
                [original_input_path],
                classification_postfix,
                self._persistence.file_extension,
                self._persistence.working_dir,
            )
            masked_heatmap_path = Model.output_path(
                [original_input_path], heatmap_postfix, self._persistence.file_extension, self._persistence.working_dir,
            )

            for i in range(rows):
                for j in range(cols):
                    if (
                        classification_matrix[i, j] == self._persistence.garbage_c_id * 100
                        or classification_matrix[i, j] == self._persistence.water_c_id * 100
                    ):
                        morphology_matrix[i, j] = 1
                    else:
                        morphology_matrix[i, j] = 0

            Model.save_tif(
                input_path=original_input_path,
                array=[morphology_matrix],
                shape=morphology_matrix.shape,
                band_count=1,
                output_path=morphology_path,
            )

            matrix = self._persistence.morphology_matrix_size, self._persistence.morphology_matrix_size
            opening = Model.morphology(
                "opening", morphology_path, opening_path, matrix=matrix
            )

            if opening is not None:
                dilation = Model.morphology(
                    "dilation", opening_path, dilation_path, iterations=self._persistence.morphology_iterations
                )

                if dilation is not None:
                    for i in range(rows):
                        for j in range(cols):
                            if dilation[i, j] == 1:
                                masked_classification[i, j] = classification_matrix[
                                    i, j
                                ]
                                masked_heatmap[i, j] = heatmap_matrix[i, j]
                            else:
                                masked_classification[i, j] = 0
                                masked_heatmap[i, j] = 0

                    Model.save_tif(
                        input_path=original_input_path,
                        array=[masked_classification],
                        shape=masked_classification.shape,
                        band_count=1,
                        output_path=masked_classification_path,
                    )

                    Model.save_tif(
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
    def get_min_max_value_of_band(input_path: str, band_number: int) -> Tuple[int, int]:
        """
        Calculates the minimum and maximum values of a band.

        :param input_path: Path of an image.
        :param band_number: Serial number of a band.
        :return: Minimum and maximum values.
        """

        with rasterio.open(input_path, "r") as img:
            band = img.read(band_number)
            min_value, max_value = np.nanmin(band), np.nanmax(band)
            return int(min_value), int(max_value)

    @staticmethod
    def calculate_indices(
        get_list: List[str], bands: Dict[str, np.ndarray]
    ) -> List[np.ndarray]:
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
                pi = Model.calculate_index(numerator=nir, denominator=nir + red)
                list_of_bands_and_indices.append(pi)
            elif item == "ndwi":
                ndwi = Model.calculate_index(
                    numerator=green - nir, denominator=green + nir
                )
                list_of_bands_and_indices.append(ndwi)
            elif item == "ndvi":
                ndvi = Model.calculate_index(
                    numerator=nir - red, denominator=nir + red
                )
                list_of_bands_and_indices.append(ndvi)
            elif item == "rndvi":
                rndvi = Model.calculate_index(
                    numerator=red - nir, denominator=red + nir
                )
                list_of_bands_and_indices.append(rndvi)
            elif item == "sr":
                sr = Model.calculate_index(numerator=nir, denominator=red)
                list_of_bands_and_indices.append(sr)
            elif item == "apwi":
                apwi = Model.calculate_index(
                    numerator=blue, denominator=1 - (red + green + nir) / 3
                )
                list_of_bands_and_indices.append(apwi)

        return list_of_bands_and_indices

    @staticmethod
    def make_noisy_data(data: pd.DataFrame) -> pd.DataFrame:
        """
        Adds noise to given dataframe
        :param data: the dataframe to add noise to
        :return: A dataframe that has noisy data added to it.
        """

        data_copy = data.copy()[
            ["BLUE", "GREEN", "RED", "NIR", "PI", "NDWI", "NDVI", "RNDVI", "SR"]
        ]
        noise = (np.random.normal(0, 0.1, data_copy.shape) * 1000).astype(int)
        data_copy = data_copy + noise
        bands = {
            "blue": np.expand_dims(data_copy["BLUE"].to_numpy(), axis=0),
            "green": np.expand_dims(data_copy["GREEN"].to_numpy(), axis=0),
            "red": np.expand_dims(data_copy["RED"].to_numpy(), axis=0),
            "nir": np.expand_dims(data_copy["NIR"].to_numpy(), axis=0),
        }

        requested_indices = [col.lower() for col in data_copy.columns]
        labels = [data["SURFACE"].to_numpy(), data["COD"].to_numpy()]
        indices = [
            id.flatten() for id in Model.calculate_indices(requested_indices, bands)
        ]
        labels_indices = [pd.Series(col) for col in labels + indices]

        data_noisy = pd.DataFrame(labels_indices).T
        data_noisy.columns = data.columns
        data_noisy.index.name = "FID"

        return data_noisy

    @staticmethod
    def get_coords_inside_polygon(
        polygon_coords: List[float], bbox_coords: Tuple[int, ...]
    ) -> List[Tuple[int, int]]:
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
    def save_tif(
        input_path: str,
        array: List[np.ndarray],
        shape: Tuple[int, int],
        band_count: int,
        output_path: str,
        new_geo_trans: Tuple[float, float] = None,
        metadata: Dict[str, str] = None,
    ) -> None:
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

            dataset = driver.Create(
                output_path, x_pixels, y_pixels, band_count, gdal.GDT_Float32
            )
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
    def calculate_index(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
        """
        Calculating an index based on given numerator and denominator.

        :param numerator: numerator matrix
        :param denominator: denominator matrix
        :return: result matrix, containing the calculated values
        """

        # variables
        index = np.ndarray(
            shape=numerator.shape,
            dtype="float32",
        )

        numerator_nan_min = np.nanmin(numerator)
        numerator_nan_max = np.nanmax(numerator)

        # calculate index
        nan_mask = np.isnan(numerator) | np.isnan(denominator)
        numerator_zero_mask = numerator == 0
        denominator_zero_mask = denominator == 0

        invalid_mask = nan_mask | (numerator_zero_mask & denominator_zero_mask)
        valid_mask = np.logical_not(invalid_mask)

        valid_denominator_non_zero_mask = valid_mask & np.logical_not(
            denominator_zero_mask
        )
        valid_denominator_zero_mask = valid_mask & denominator_zero_mask

        numerator_positive_denominator_zero_mask = valid_denominator_zero_mask & (
            numerator > 0
        )
        numerator_negative_denominator_zero_mask = valid_denominator_zero_mask & (
            numerator < 0
        )

        index[invalid_mask] = float("NaN")
        index[numerator_positive_denominator_zero_mask] = numerator_nan_max
        index[numerator_negative_denominator_zero_mask] = numerator_nan_min
        index[valid_denominator_non_zero_mask] = (
            numerator[valid_denominator_non_zero_mask]
            / denominator[valid_denominator_non_zero_mask]
        )

        # return index values
        return index

    @staticmethod
    def output_path(
        input_paths: List[str],
        postfix: str,
        output_file_extension: str,
        working_dir: str = "",
    ) -> str:
        """
        Returns generated output path from given parameters.

        :param input_paths: list of input file paths
        :param postfix: postfix of output file
        :param output_file_extension: file extension of output file
        :param working_dir: path to working directory
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
            output_path = (
                working_dir
                + "/"
                + "_".join(file_names)
                + postfix
                + "."
                + output_file_extension
            )
        return output_path

    @staticmethod
    def resolve_bands_indices_string(string: str) -> List[str]:
        """
        Resolves band strings.

        :param string: name of band/indices separated by "-", or "all", "all_no_blue", "bands", "indices"
        :return: list containing the band/index values
        """

        string_list = string.lower().split("-")

        if "all" in string_list:
            return [
                "blue",
                "green",
                "red",
                "nir",
                "pi",
                "ndwi",
                "ndvi",
                "rndvi",
                "sr",
                "apwi",
            ]
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
    def get_coords_of_pixel(
        i: int, j: int, gt: Tuple[int, ...]
    ) -> Tuple[float, float]:
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
    def get_bbox_of_pixel(
            i: int, j: int, gt: Tuple[int, ...]
    ) -> List[Tuple[float, float]]:
        """
        Calculates the bounding box of a single pixel.

        :param i: Row index.
        :param j: Column index.
        :param gt: GeoTransform of the picture.
        :return: Bounding box of a pixel.
        """

        x_size = gt[1]
        y_size = -gt[5]

        upper_left = Model.get_coords_of_pixel(i, j, gt)
        upper_right = upper_left[0] + x_size, upper_left[1]
        bottom_right = upper_left[0] + x_size, upper_left[1] - y_size
        bottom_left = upper_left[0], upper_left[1] - y_size

        bbox = [upper_left, upper_right, bottom_right, bottom_left]

        return bbox

    @staticmethod
    def get_bbox_of_all_given_values(input_file: str, value: int) -> List:
        """
        Calculates all bounding boxes of all pixels.

        :param input_file: Path of input file.
        :param value: Numerical value of the pixels.
        :return: List of bounding boxes.
        """

        dataset = gdal.Open(input_file, gdal.GA_ReadOnly)
        values = dataset.GetRasterBand(1).ReadAsArray()
        gt = dataset.GetGeoTransform()

        all_bboxes = list()
        rows, cols = values.shape

        for i in range(rows):
            for j in range(cols):
                if values[i, j] != value:
                    continue
                else:
                    bbox = Model.get_bbox_of_pixel(i, j, gt)
                    all_bboxes.append(bbox)

        dataset = None

        return all_bboxes

    @staticmethod
    def get_waste_geojson(input_file: str, output_file: str, search_value: int) -> None:
        """
        Unites the adjacent pixels, then creates a GeoJSON file containing the result polygons.

        :param input_file: Path of input file.
        :param output_file: Path of output file.
        :param search_value: Numerical value of the pixels.
        :return:
        """

        all_bboxes = Model.get_bbox_of_all_given_values(input_file, search_value)

        ds = gdal.Open(input_file, gdal.GA_ReadOnly)
        srs_wkt = ds.GetProjection()
        srs_converter = osr.SpatialReference()
        srs_converter.ImportFromWkt(srs_wkt)

        ds = None

        features = list()
        polygon_id = 1

        for bbox in all_bboxes:
            bbox.append(bbox[0])

            coords = list(map(list, bbox))

            bbox_transformed = list(map(tuple, coords))

            polygon = geojson.Polygon([bbox_transformed])

            features.append(
                geojson.Feature(geometry=polygon, properties={"id": str(polygon_id)})
            )

            polygon_id += 1

        feature_collection = geojson.FeatureCollection(features)

        polygons = list()
        for elem in feature_collection["features"]:
            polygon = shape(elem["geometry"])
            polygons.append(polygon)

        if polygons:
            boundary = gpd.GeoSeries(unary_union(polygons))
            boundary = boundary.__geo_interface__
            boundary["crs"] = {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:EPSG::3857"},
            }
        else:
            boundary = {"type": "FeatureCollection", "features": []}

        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_file, "w") as file:
            geojson.dump(boundary, file)

    @staticmethod
    def convert_multipolygons_to_polygons(data_file: Dict) -> Dict:
        """
        Converts MultiPolygon shapes to Polygons.

        :param data_file: Dictionary containing the AOIs in GeoJSON format.
        :return: Converted version of data_file.
        """

        new_data_file = copy.deepcopy(data_file)

        for feature in new_data_file["features"]:
            if feature["geometry"]["type"] == "MultiPolygon":
                feature["geometry"]["type"] = "Polygon"
                feature["geometry"]["coordinates"] = feature["geometry"]["coordinates"][
                    0
                ]

        return new_data_file

    @staticmethod
    def transform_list_of_coordinates_to_crs(
            coords: List[List[int]], crs_from: str, crs_to: str
    ) -> List[List[int]]:
        """
        Transforms coordinates from one CRS to another.

        :param coords: List of coordinates: [[x1, y1], [x2, y2], ...].
        :param crs_from: Projection of input data.
        :param crs_to: Projection of output data.
        :return: List of transformed coordinates.
        """

        transformed_coords = copy.deepcopy(coords)

        transformer = pyproj.Transformer.from_crs(
            crs_from=crs_from, crs_to=crs_to, always_xy=True
        )

        for i in range(len(coords)):
            x, y = coords[i]
            new_x, new_y = transformer.transform(x, y)
            transformed_coords[i][0] = new_x
            transformed_coords[i][1] = new_y

        return transformed_coords

    @staticmethod
    def transform_dict_of_coordinates_to_crs(data_file: Dict, crs_to: str) -> Dict:
        """
        Transforms all coordinates from their CRS to wanted CRS.

        :param data_file: Dictionary containing the geometries in GeoJSON format.
        :param crs_to: Projection of output data.
        :return: Transformed version of data_file.
        """

        transformed_data_file = copy.deepcopy(data_file)
        for feature in transformed_data_file["features"]:
            crs_from = "epsg:4326"
            if "crs" in transformed_data_file.keys():
                crs_from = transformed_data_file["crs"]["properties"]["name"]

            coordinates = feature["geometry"]["coordinates"][0]

            transformed_coords = Model.transform_list_of_coordinates_to_crs(
                coordinates, crs_from, crs_to
            )

            feature["geometry"]["coordinates"] = [transformed_coords]

        transformed_data_file["crs"] = dict()
        transformed_data_file["crs"]["properties"] = dict()
        transformed_data_file["crs"]["properties"]["name"] = crs_to

        return transformed_data_file

    @staticmethod
    def calculate_coords_for_pixels(input_path: str) -> Union[np.ndarray, None]:
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
                    coords_xy[i, j] = Model.get_coords_of_pixel(i, j, gt)

            return coords_xy
        finally:
            del ds

    @staticmethod
    def get_empty_intersection_matrix_and_start_coords(
        input_path_1: str, input_path_2: str
    ) -> Union[Tuple[np.ndarray, Tuple], Tuple[None, None]]:
        """
        Calculates the intersection of two different sized matrices.

        :param input_path_1: path of the first input image
        :param input_path_2: path of the second input image
        :return: empty intersection matrix, coordinate information for later use
        """

        coords_1 = Model.calculate_coords_for_pixels(input_path_1)
        coords_2 = Model.calculate_coords_for_pixels(input_path_2)

        if (coords_1 is not None) and (coords_2 is not None):
            img_1_size = coords_1.shape[0] * coords_1.shape[1]
            img_2_size = coords_2.shape[0] * coords_2.shape[1]

            larger_img = coords_1 if img_1_size >= img_2_size else coords_2
            smaller_img = coords_1 if img_1_size < img_2_size else coords_2

            selector = np.in1d(larger_img.flatten(), smaller_img.flatten())
            intersection = list(compress(range(len(selector)), selector))

            new_rows, new_cols = 0, 0

            if intersection:
                larger_rows, larger_cols = np.unravel_index(
                    intersection, larger_img.shape
                )
                larger_start_index = (larger_rows[0], larger_cols[0])

                start_coord = larger_img[larger_start_index]

                smaller_start_index = np.where(smaller_img == start_coord)
                smaller_start_index = (
                    smaller_start_index[0][0],
                    smaller_start_index[1][0],
                )

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

                coords_information = (
                    start_coord,
                    larger_start_index,
                    smaller_start_index,
                )

                return intersection_matrix, coords_information

        return None, None

    def create_classification_and_heatmap_with_random_forest(
        self,
        input_path: str,
        clf: RandomForestClassifier,
        classification_postfix: str,
        heatmap_postfix: str,
    ) -> Tuple[str, str]:
        """
        Creates classification and garbage heatmap with Random Forest Classifier.

        :param input_path: input path of the image to be processed
        :param clf: an instance of RandomForestClassifier
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
            array_df = pd.DataFrame(array, dtype="float32")

            split_size = ceil(
                array_df.shape[0]
                / ceil((array_df.shape[0] * self._persistence.max_class_count) / self._persistence.max_class_value_count)
            )
            split_count = ceil(
                (array_df.shape[0] * self._persistence.max_class_count) / self._persistence.max_class_value_count
            )
            for c in range(split_count):
                new_array_df = array_df[c * split_size : (c + 1) * split_size].dropna(
                    axis="index"
                )
                pred_proba = clf.predict_proba(new_array_df)

                counter = 0
                for i in range(c * split_size, (c + 1) * split_size):
                    if i == rows * cols:
                        break

                    if np.any(np.isnan(array[i])):
                        continue

                    max_ind = np.argmax(pred_proba[counter])
                    max_value = pred_proba[counter][max_ind]

                    class_str = str(classes[max_ind])
                    if class_str == (str(self._persistence.garbage_c_id * 100)):
                        if max_value >= self._persistence.high_prob_percent / 100:
                            heatmap[i] = self._persistence.high_prob_value
                        elif (
                            self._persistence.medium_prob_percent / 100
                            <= max_value
                            < self._persistence.high_prob_percent / 100
                        ):
                            heatmap[i] = self._persistence.medium_prob_value
                        elif (
                            self._persistence.low_prob_percent / 100
                            <= max_value
                            < self._persistence.medium_prob_percent / 100
                        ):
                            heatmap[i] = self._persistence.low_prob_value

                    classification[i] = classes[max_ind]

                    counter += 1

            classification = classification.reshape((rows, cols))
            heatmap = heatmap.reshape((rows, cols))

            classification_output_path = Model.output_path(
                [input_path], classification_postfix, self._persistence.file_extension, self._persistence.working_dir,
            )
            heatmap_output_path = Model.output_path(
                [input_path], heatmap_postfix, self._persistence.file_extension, self._persistence.working_dir,
            )

            # save classification
            Model.save_tif(
                input_path=input_path,
                array=[classification],
                shape=classification.shape,
                band_count=1,
                output_path=classification_output_path,
            )

            # save heatmap
            Model.save_tif(
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
    def morphology(
        morph_type: str,
        path: str,
        output: str,
        matrix: Tuple[int, int] = (3, 3),
        iterations: int = 1,
    ) -> Union[np.ndarray, None]:
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

            Model.save_tif(
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
    def valid_row(shape: Tuple[int, int], row: int) -> bool:
        """
        Decides whether the given row is inside the array with the given shape, or not.
        Source: https://playandlearntocode.com/article/flood-fill-algorithm-in-python

        :param shape: shape of the array
        :param row: index of the row
        :return: True or False
        """

        return 0 <= row < shape[0]

    @staticmethod
    def valid_col(shape: Tuple[int, int], col: int) -> bool:
        """
        Decides whether the given column is inside the array with the given shape, or not.
        Source: https://playandlearntocode.com/article/flood-fill-algorithm-in-python

        :param shape: shape of the array
        :param col: index of the column
        :return: True or False
        """

        return 0 <= col < shape[1]

    @staticmethod
    def is_search_value(
        matrix: np.ndarray, row: int, col: int, search_value: List[int]
    ) -> bool:
        """
        Checks whether the value of the given pixel is the expected value or not.
        Source: https://playandlearntocode.com/article/flood-fill-algorithm-in-python

        :param matrix: an array of a classified image or a heatmap image
        :param row: row index
        :param col: column index
        :param search_value: the expected value
        :return: True or False
        """

        if not Model.valid_row(matrix.shape, row):
            return False

        if not Model.valid_col(matrix.shape, col):
            return False

        if matrix[row, col] in search_value:
            return True
        else:
            return False

    @staticmethod
    def iterative_flood_fill(
        matrix: np.ndarray, row: int, col: int, search_value: List[int]
    ) -> Union[List[Tuple[int, int]], None]:
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

        if not Model.valid_row(matrix.shape, row):
            return

        if not Model.valid_col(matrix.shape, col):
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

            if Model.is_search_value(matrix, cur_row - 1, cur_col, search_value):
                matrix[cur_row - 1, cur_col] = -1
                q.append([cur_row - 1, cur_col])

            if Model.is_search_value(matrix, cur_row + 1, cur_col, search_value):
                matrix[cur_row + 1, cur_col] = -1
                q.append([cur_row + 1, cur_col])

            if Model.is_search_value(matrix, cur_row, cur_col - 1, search_value):
                matrix[cur_row, cur_col - 1] = -1
                q.append([cur_row, cur_col - 1])

            if Model.is_search_value(matrix, cur_row, cur_col + 1, search_value):
                matrix[cur_row, cur_col + 1] = -1
                q.append([cur_row, cur_col + 1])

        return region

    @staticmethod
    def find_regions(
        matrix: np.ndarray, search_value: List[int]
    ) -> List[List[Tuple[int, int]]]:
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
                    region = Model.iterative_flood_fill(matrix, row, col, search_value)
                    if not (region is None):
                        all_regions.append(region)

        return all_regions

    @staticmethod
    def get_bbox_indices_of_region(
        region: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
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

        bbox = [
            (min_row, min_col),
            (min_row, max_col),
            (max_row, max_col),
            (max_row, min_col),
        ]

        return bbox

    @staticmethod
    def get_bbox_indices_of_all_regions(
        all_regions: List[List[Tuple[int, int]]]
    ) -> List[List[Tuple[int, int]]]:
        """
        Returns the indices of the bounding boxes of all the given regions.

        :param all_regions: list of regions
        :return: list containing the indices of bounding boxes of the regions
        """

        bboxes = list()

        for region in all_regions:
            bbox = Model.get_bbox_indices_of_region(region)
            bboxes.append(bbox)

        return bboxes

    @staticmethod
    def get_bbox_coordinates_of_same_areas(
        input_path: str, search_value: List[int]
    ) -> Union[List[List[Tuple[int, ...]]], None]:
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

            regions = Model.find_regions(matrix, search_value)
            bboxes = Model.get_bbox_indices_of_all_regions(regions)
            bbox_coords = list()

            for bbox in bboxes:
                coords = list()

                upper_left = Model.get_coords_of_pixel(bbox[0][0], bbox[0][1], gt)
                upper_right = Model.get_coords_of_pixel(bbox[1][0], bbox[1][1], gt)
                bottom_right = Model.get_coords_of_pixel(bbox[2][0], bbox[2][1], gt)
                bottom_left = Model.get_coords_of_pixel(bbox[3][0], bbox[3][1], gt)

                coords.append(upper_left)
                coords.append((upper_right[0] + pixel_size_x, upper_right[1]))
                coords.append(
                    (bottom_right[0] + pixel_size_x, bottom_right[1] - pixel_size_y)
                )
                coords.append((bottom_left[0], bottom_left[1] - pixel_size_y))

                bbox_coords.append(coords)

            return bbox_coords
        except Exception:
            return None
        finally:
            del dataset
