import os
import copy
import pyproj
import geojson
import rasterio
import cv2 as cv
import numpy as np
import pandas as pd
import geopandas as gpd

from osgeo import osr
from math import ceil
from osgeo import gdal
from shapely.geometry import shape
from shapely.ops import unary_union
from sklearn.ensemble import RandomForestClassifier
from typing import List, Tuple, Union, Dict


class Model(object):
    """
    Class for application logic.

    """

    def __init__(self, config_file: Dict) -> None:
        """
        Constructor of Model class.

        """

        super(Model, self).__init__()

        self.config_file = config_file

        self.satellite_type = self.config_file["satellite_type"]
        self.garbage_c_id = int(self.config_file["garbage_c_id"])
        self.water_c_id = int(self.config_file["water_c_id"])
        self.morphology_matrix_size = int(self.config_file["morphology_matrix_size"])
        self.morphology_iterations = int(self.config_file["morphology_iterations"])
        self.max_class_count = int(self.config_file["max_class_count"])
        self.max_class_value_count = int(self.config_file["max_class_value_count"])
        self.low_prob_percent = int(self.config_file["low_prob_percent"])
        self.medium_prob_percent = int(self.config_file["medium_prob_percent"])
        self.high_prob_percent = int(self.config_file["high_prob_percent"])
        self.low_prob_value = int(self.config_file["low_prob_value"])
        self.medium_prob_value = int(self.config_file["medium_prob_value"])
        self.high_prob_value = int(self.config_file["high_prob_value"])
        self.classification_postfix = self.config_file["classification_postfix"]
        self.heatmap_postfix = self.config_file["heatmap_postfix"]
        self.masked_classification_postfix = self.config_file["masked_classification_postfix"]
        self.masked_heatmap_postfix = self.config_file["masked_heatmap_postfix"]
        self.file_extension = self.config_file["file_extension"]

        self.pixel_size_x = None
        self.pixel_size_y = None

        if self.satellite_type.lower() == "PlanetScope".lower():
            self.pixel_size_x = self.pixel_size_y = 3
        elif self.satellite_type.lower() == "Sentinel-2".lower():
            self.pixel_size_x = self.pixel_size_y = 10

    def create_classification_and_heatmap_with_random_forest(self,
                                                             input_path: str,
                                                             clf: RandomForestClassifier) -> Tuple[str, str]:
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

            split_size = ceil(array_df.shape[0] /
                              ceil((array_df.shape[0] * self.max_class_count) / self.max_class_value_count))

            split_count = ceil((array_df.shape[0] * self.max_class_count) / self.max_class_value_count)

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

                    if classes[max_ind] == self.garbage_c_id * 100:
                        if max_value >= self.high_prob_percent / 100:
                            heatmap[i] = self.high_prob_value
                        elif self.medium_prob_percent / 100 <= max_value < self.high_prob_percent / 100:
                            heatmap[i] = self.medium_prob_value
                        elif self.low_prob_percent / 100 <= max_value < self.medium_prob_percent / 100:
                            heatmap[i] = self.low_prob_value

                    classification[i] = classes[max_ind]

                    counter += 1

            classification = classification.reshape((rows, cols))
            heatmap = heatmap.reshape((rows, cols))

            classification_output_path = Model.output_path(input_path, self.classification_postfix, self.file_extension)
            heatmap_output_path = Model.output_path(input_path, self.heatmap_postfix, self.file_extension)

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
        finally:
            del ds

    def get_satellite_band(self, band: str) -> int:
        """
        Returns the given satellite's band index.

        :param band: name of satellite band
        :return: index of given satellite band
        :raise NameError: if wrong satellite name is given
        """

        satellite_name = self.satellite_type.lower()
        band_name = band.lower()

        index = satellite_name + "_" + band_name

        if index in self.config_file.keys():
            return int(self.config_file[index])
        else:
            raise NameError("Wrong satellite or band name!")

    def get_bands_indices(self, input_path: str, get: str) -> List[np.ndarray]:
        """
        Returns a list of arrays, containing the band values and/or calculated index values.

        :param input_path: path of the input image
        :param get: name of band/indices
        :return: band values and/or index values
        """

        get_list = Model.resolve_bands_indices_string(get)

        with rasterio.open(input_path, "r") as img:
            blue_ind = self.get_satellite_band("Blue")
            green_ind = self.get_satellite_band("Green")
            red_ind = self.get_satellite_band("Red")
            nir_ind = self.get_satellite_band("NIR")

            blue = (img.read(blue_ind)).astype(dtype="float32")
            green = (img.read(green_ind)).astype(dtype="float32")
            red = (img.read(red_ind)).astype(dtype="float32")
            nir = (img.read(nir_ind)).astype(dtype="float32")

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
                    ndwi = Model.calculate_index(numerator=green - nir, denominator=green + nir)
                    list_of_bands_and_indices.append(ndwi)
                elif item == "ndvi":
                    ndvi = Model.calculate_index(numerator=nir - red, denominator=nir + red)
                    list_of_bands_and_indices.append(ndvi)
                elif item == "rndvi":
                    rndvi = Model.calculate_index(numerator=red - nir, denominator=red + nir)
                    list_of_bands_and_indices.append(rndvi)
                elif item == "sr":
                    sr = Model.calculate_index(numerator=nir, denominator=red)
                    list_of_bands_and_indices.append(sr)

            return list_of_bands_and_indices

    def save_bands_indices(self, input_path: str, save: str, postfix: str) -> str:
        """
        Saves the specified band values and/or index values to a single- or multi-band tif file.

        :param input_path: path of the input image
        :param save: name of band/indices
        :param postfix: postfix of output file name
        :return: path of the output image
        """

        list_of_bands_and_indices = self.get_bands_indices(
            input_path=input_path,
            get=save,
        )

        bands = len(list_of_bands_and_indices)
        output_path = Model.output_path(input_path, postfix, self.file_extension)

        Model.save_tif(
            input_path=input_path,
            array=list_of_bands_and_indices,
            shape=list_of_bands_and_indices[0].shape,
            band_count=bands,
            output_path=output_path,
        )

        return output_path

    def estimate_garbage_area(
            self, input_path: str, image_type: str) -> float:
        """
        Estimates the area covered by garbage, based on the pixel size of a picture.

        :param input_path: input path of classified picture
        :param image_type: "classified" or "heatmap"
        :return: estimated area if it can be calculated, 0 otherwise
        :raise NotEnoughBandsException: if the image to be opened does not have only one band
        :raise CodValueNotPresentException: if the Garbage Class is not present on the image
        :raise InvalidClassifiedImageException: if not all values could be divided by 100 on the classified image
        """

        try:
            dataset = gdal.Open(input_path, gdal.GA_ReadOnly)

            band = dataset.GetRasterBand(1)
            band = band.ReadAsArray()
            unique_values = np.unique(band)

            rows, cols = band.shape
            area = 0.0

            if image_type.lower() == "classified":
                if self.garbage_c_id * 100 not in unique_values:
                    return 0

                cond_list = [value % 100 == 0 for value in unique_values]

                if not all(cond_list):
                    return 0

                for i in range(rows):
                    for j in range(cols):
                        if band[i, j] == self.garbage_c_id * 100:
                            area += self.pixel_size_x * self.pixel_size_y
            elif image_type.lower() == "heatmap":
                for i in range(rows):
                    for j in range(cols):
                        if band[i, j] == self.low_prob_value or \
                           band[i, j] == self.medium_prob_value or \
                           band[i, j] == self.high_prob_value:
                            area += self.pixel_size_x * self.pixel_size_y

            return area
        finally:
            del dataset

    def create_masked_classification_and_heatmap(self, original_input_path: str, classification_path: str,
                                                 heatmap_path: str) -> Tuple[str, str]:
        """
        Creates the masked classification and masked heatmap based on the input classification and input heatmap.
        Uses morphological transformations (opening and dilation).

        :param original_input_path: input path of source image
        :param classification_path: path of the classified image
        :param heatmap_path: path of the heatmap image
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
            morphology_path = self.output_path(original_input_path, "morphology", self.file_extension)
            opening_path = self.output_path(original_input_path, "morphology_opening", self.file_extension)
            dilation_path = self.output_path(original_input_path, "morphology_opening_dilation", self.file_extension)
            masked_classification_path = self.output_path(original_input_path, self.masked_classification_postfix,
                                                          self.file_extension)
            masked_heatmap_path = self.output_path(original_input_path, self.masked_heatmap_postfix,
                                                   self.file_extension)

            for i in range(rows):
                for j in range(cols):
                    if classification_matrix[i, j] == self.garbage_c_id * 100 or \
                       classification_matrix[i, j] == self.water_c_id * 100:
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

            matrix = self.morphology_matrix_size, self.morphology_matrix_size
            opening = Model.morphology("opening", morphology_path, opening_path, matrix=matrix)
            if opening is not None:
                dilation = Model.morphology("dilation", opening_path,
                                            dilation_path, iterations=self.morphology_iterations)
                if dilation is not None:
                    for i in range(rows):
                        for j in range(cols):
                            if dilation[i, j] == 1:
                                masked_classification[i, j] = classification_matrix[i, j]
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
    def get_coords_of_pixel(i: int, j: int, gt: Tuple[int, ...]) -> Tuple[float, float]:
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
    def get_bbox_of_pixel(i, j, gt):
        x_size = gt[1]
        y_size = -gt[5]

        upper_left = Model.get_coords_of_pixel(i, j, gt)
        upper_right = upper_left[0] + x_size, upper_left[1]
        bottom_right = upper_left[0] + x_size, upper_left[1] - y_size
        bottom_left = upper_left[0], upper_left[1] - y_size

        bbox = [upper_left, upper_right, bottom_right, bottom_left]

        return bbox

    @staticmethod
    def get_bbox_of_all_given_values(input_file, value):
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
    def get_waste_geojson(input_file, output_file, search_value):
        all_bboxes = Model.get_bbox_of_all_given_values(input_file, search_value)

        ds = gdal.Open(input_file, gdal.GA_ReadOnly)
        srs_wkt = ds.GetProjection()
        srs_converter = osr.SpatialReference()
        srs_converter.ImportFromWkt(srs_wkt)
        srs_for_pyproj = srs_converter.ExportToProj4()

        ds = None

        input_crs = srs_for_pyproj
        output_crs = "EPSG:3857"

        features = list()
        polygon_id = 1

        for bbox in all_bboxes:
            bbox.append(bbox[0])

            coords = list(map(list, bbox))

            new_coords = Model.transform_coordinates(coords, input_crs, output_crs)

            bbox_transformed = list(map(tuple, new_coords))

            polygon = geojson.Polygon([bbox_transformed])

            features.append(geojson.Feature(geometry=polygon, properties={"id": str(polygon_id)}))

            polygon_id += 1

        feature_collection = geojson.FeatureCollection(features)

        polygons = list()
        for elem in feature_collection["features"]:
            polygon = shape(elem["geometry"])
            polygons.append(polygon)

        if polygons:
            boundary = gpd.GeoSeries(unary_union(polygons))
            boundary = boundary.__geo_interface__
            boundary["crs"] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3857"}}
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

        :param data_file: dictionary containing the AOIs in GeoJSON format
        :return: converted version of data_file
        """

        new_data_file = copy.deepcopy(data_file)

        for feature in new_data_file["features"]:
            if feature["geometry"]["type"] == "MultiPolygon":
                feature["geometry"]["type"] = "Polygon"
                feature["geometry"]["coordinates"] = feature["geometry"]["coordinates"][0]

        return new_data_file

    @staticmethod
    def transform_coordinates(coords: List[List[int]], input_crs: str, output_crs: str) -> List[List[int]]:
        """
        Transforms coordinates from one CRS to another.

        :param coords: list of coordinates: [[x1, y1], [x2, y2], ...]
        :param input_crs: original CRS of coordinates
        :param output_crs: wanted CRS of coordinates
        :return: list of transformed coordinates
        """

        transformed_coords = copy.deepcopy(coords)

        transformer = pyproj.Transformer.from_crs(crs_from=input_crs, crs_to=output_crs, always_xy=True)

        for i in range(len(coords)):
            x, y = coords[i]
            new_x, new_y = transformer.transform(x, y)
            transformed_coords[i][0] = new_x
            transformed_coords[i][1] = new_y

        return transformed_coords

    @staticmethod
    def transform_coordinates_to_wgs84(data_file: Dict) -> Dict:
        """
        Transforms all coordinates from given CRS to WGS84.

        :param data_file: dictionary containing the AOIs in GeoJSON format
        :return: transformed version of data_file
        """

        if "crs" in data_file.keys() and data_file["crs"]["properties"]["name"] != "urn:ogc:def:crs:OGC:1.3:CRS84":
            transformed_data_file = copy.deepcopy(data_file)
            for feature in transformed_data_file["features"]:

                input_crs = transformed_data_file["crs"]["properties"]["name"]
                output_crs = "epsg:4326"

                coordinates = feature["geometry"]["coordinates"][0]

                transformed_coords = Model.transform_coordinates(coordinates, input_crs, output_crs)

                feature["geometry"]["coordinates"] = [transformed_coords]

            transformed_data_file["crs"]["properties"]["name"] = "urn:ogc:def:crs:OGC:1.3:CRS84"

            return transformed_data_file
        else:
            return data_file

    @staticmethod
    def resolve_bands_indices_string(string: str) -> List[str]:
        """
        Resolves band strings.

        :param string: name of band/indices separated by "-", or "all", "bands", "indices"
        :return: list containing the band/index values
        """

        string_list = string.lower().split("-")

        if "all" in string_list:
            return ["blue", "green", "red", "nir", "pi", "ndwi", "ndvi", "rndvi", "sr"]
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

        return bands_indices

    @staticmethod
    def output_path(input_path: str, postfix: str, output_file_extension: str) -> str:
        """
        Creates the output path of result images.

        :param input_path: path of original image
        :param postfix: file name postfix for result image
        :param output_file_extension: the wanted file extension of result image
        :return: output path
        """

        filename, file_extension = os.path.splitext(input_path)
        output_path = filename + "_" + postfix + "." + output_file_extension
        return output_path

    @staticmethod
    def calculate_index(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
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

        # calculate index
        for i in range(rows):
            for j in range(cols):
                if np.isnan(numerator[i, j]) or np.isnan(denominator[i, j]):
                    index[i, j] = float("NaN")
                elif denominator[i, j] != 0:
                    index[i, j] = numerator[i, j] / denominator[i, j]
                else:
                    if numerator[i, j] < 0:
                        index[i, j] = np.nanmin(numerator)
                    elif numerator[i, j] > 0:
                        index[i, j] = np.nanmax(numerator)
                    else:
                        index[i, j] = float("NaN")

        # return index values
        return index

    @staticmethod
    def save_tif(
            input_path: str, array: List[np.ndarray], shape: Tuple[int, int],
            band_count: int, output_path: str, new_geo_trans: Tuple[float, float] = None) -> None:
        """
        Saves arrays (1 or more) to a georeferenced tif file.

        :param input_path: georeferenced input image
        :param array: list of arrays to be saved
        :param shape: shape of the output image
        :param band_count: number of bands in the output tif file
        :param output_path: path of the output image
        :param new_geo_trans: other GeoTransform if it is needed
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

            for band in range(band_count):
                outband = dataset.GetRasterBand(band + 1)
                outband.WriteArray(array[band][:, :])
                outband.SetNoDataValue(float("NaN"))
                outband.FlushCache()

            dataset.FlushCache()
        finally:
            del img_gdal

    @staticmethod
    def morphology(morph_type: str, path: str, output: str,
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
