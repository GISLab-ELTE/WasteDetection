from collections import OrderedDict
from typing import List
import numpy as np


class IndexCalculator(object):
    @staticmethod
    def calculate_indices(index_names: List[str], bands: OrderedDict) -> OrderedDict:
        """
        Calculates indices using the given satellite bands
        :param index_names: list of indices to be calculated
        :param bands: a dictionary of bands.

        :returns: a list containing all the indices in the order in which they got requested.
        """

        indices = OrderedDict()
        for index_name in index_names:
            indices[index_name] = IndexCalculator.calculate_index(index_name, bands, indices)

        return indices

    @staticmethod
    def calculate_index(index: str, bands: OrderedDict, indices: OrderedDict) -> np.ndarray:
        if index == "pi":
            return IndexCalculator.calculate_pi(bands["red"], bands["nir"])
        if index == "ndwi":
            return IndexCalculator.calculate_ndwi(bands["green"], bands["nir"])
        if index == "ndvi":
            return IndexCalculator.calculate_ndvi(bands["red"], bands["nir"])
        if index == "rndvi":
            return IndexCalculator.calculate_rndvi(bands["red"], bands["nir"])
        if index == "sr":
            return IndexCalculator.calculate_sr(bands["red"], bands["nir"])
        if index == "apwi":
            return IndexCalculator.calculate_apwi(bands["blue"], bands["green"], bands["red"], bands["nir"])
        if index == "mndbi":
            return IndexCalculator.calculate_mndbi(bands["swir"], bands["nir"])
        if index == "api":
            return IndexCalculator.calculate_api(indices["pi"], indices["ndvi"], indices["mndbi"])

        raise ValueError(f"Unknown index: {index}")

    @staticmethod
    def calculate_pi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Formula:
        PI = NIR / (NIR + RED)

        :param red: Red band values
        :param nir: NIR band values
        :return: Computed PI values
        """
        return IndexCalculator.calculate_fraction(numerator=nir, denominator=nir + red)

    @staticmethod
    def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Formula:
        NDWI = (GREEN - NIR) / (GREEN + NIR)

        :param green: Green band values
        :param nir: NIR band values
        :return: Computed NDWI values
        """
        return IndexCalculator.calculate_fraction(numerator=green - nir, denominator=green + nir)

    @staticmethod
    def calculate_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Formula:
        NDVI = (NIR - RED) / (NIR + RED)

        :param red: Red band values
        :param nir: NIR band values
        :return: Computed NDVI values
        """
        return IndexCalculator.calculate_fraction(numerator=nir - red, denominator=nir + red)

    @staticmethod
    def calculate_rndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Formula:
        RNDVI = (RED - NIR) / (RED + NIR)

        :param red: Red band values
        :param nir: NIR band values
        :return: Computed RNDVI values
        """
        return IndexCalculator.calculate_fraction(numerator=red - nir, denominator=red + nir)

    @staticmethod
    def calculate_sr(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Formula:
        SR = NIR / RED

        :param red: Red band values
        :param nir: NIR band values
        :return: Computed SR values
        """
        return IndexCalculator.calculate_fraction(numerator=nir, denominator=red)

    @staticmethod
    def calculate_apwi(blue: np.ndarray, green: np.ndarray, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Formula:
        APWI = BLUE / (1 - (RED + GREEN + NIR) / 3)

        :param blue: Blue band values
        :param green: Green band values
        :param red: Red band values
        :param nir: NIR band values
        :return: Computed APWI values
        """
        return IndexCalculator.calculate_fraction(numerator=blue, denominator=1 - (red + green + nir) / 3)

    @staticmethod
    def calculate_mndbi(swir: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Formula:
        MNDBI = (SWIR - NIR) / (SWIR + NIR)

        :param swir: SWIR band values
        :param nir: NIR band values
        :return: Computed MNDBI values
        """
        return IndexCalculator.calculate_fraction(numerator=swir - nir, denominator=swir + nir)

    @staticmethod
    def calculate_api(pi: np.ndarray, ndvi: np.ndarray, mndbi: np.ndarray) -> np.ndarray:
        """
        Formula:
        API = PI_2 where:
            - PI_1 = if NDVI > 0 then PI - NDVI else PI
            - PI_2 = if MNDBI > 0 then PI_1 - MNDBI else PI_1

        :param pi: PI values
        :param ndvi: NDVI values
        :param mndbi: MNDBI values
        :return: Computed API values
        """
        api = pi.copy()
        ndvi_mask = ndvi > 0
        api[ndvi_mask] -= ndvi[ndvi_mask]
        mndbi_mask = mndbi > 0
        api[mndbi_mask] -= mndbi[mndbi_mask]
        return api

    @staticmethod
    def calculate_fraction(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
        """
        Calculates a fraction based on given numerator and denominator matrices.

        :param numerator: numerator matrix
        :param denominator: denominator matrix
        :return: result matrix, containing the calculated values
        """
        index = np.ndarray(
            shape=numerator.shape,
            dtype="float32",
        )

        numerator_nan_min = np.nanmin(numerator)
        numerator_nan_max = np.nanmax(numerator)

        nan_mask = np.isnan(numerator) | np.isnan(denominator)
        numerator_zero_mask = numerator == 0
        denominator_zero_mask = denominator == 0

        invalid_mask = nan_mask | (numerator_zero_mask & denominator_zero_mask)
        valid_mask = np.logical_not(invalid_mask)

        valid_denominator_non_zero_mask = valid_mask & np.logical_not(denominator_zero_mask)
        valid_denominator_zero_mask = valid_mask & denominator_zero_mask

        numerator_positive_denominator_zero_mask = valid_denominator_zero_mask & (numerator > 0)
        numerator_negative_denominator_zero_mask = valid_denominator_zero_mask & (numerator < 0)

        index[invalid_mask] = float("NaN")
        index[numerator_positive_denominator_zero_mask] = numerator_nan_max
        index[numerator_negative_denominator_zero_mask] = numerator_nan_min
        index[valid_denominator_non_zero_mask] = (
            numerator[valid_denominator_non_zero_mask] / denominator[valid_denominator_non_zero_mask]
        )

        # return index values
        return index
