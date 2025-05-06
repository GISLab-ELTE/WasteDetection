from collections import OrderedDict
import unittest
import numpy as np

from model.index_calculator import IndexCalculator


class TestIndexCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.shape = (3, 3)

    def test_calculate_fraction_all_nan(self):
        numerator = np.ndarray(
            shape=self.shape,
            dtype="float64",
        )

        denominator = np.ndarray(
            shape=self.shape,
            dtype="float64",
        )

        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                numerator[i, j] = float("NaN")
                denominator[i, j] = float("NaN")

        result = IndexCalculator.calculate_fraction(numerator, denominator)

        self.assertTrue(np.array_equal(result, numerator, equal_nan=True))
        self.assertTrue(np.array_equal(result, denominator, equal_nan=True))

    def test_calculate_fraction_all_not_nan(self):
        numerator = np.ndarray(
            shape=self.shape,
            dtype="float64",
        )

        denominator = np.ndarray(
            shape=self.shape,
            dtype="float64",
        )

        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                numerator[i, j] = i + j + 1
                denominator[i, j] = i + j + 1

        result = IndexCalculator.calculate_fraction(numerator, denominator)

        self.assertTrue(np.all(result == 1))

    def test_calculate_fraction_numerator_negative_denominator_zeros(self):
        numerator = np.ndarray(
            shape=self.shape,
            dtype="float64",
        )

        denominator = np.zeros(
            shape=self.shape,
            dtype="float64",
        )

        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                numerator[i, j] = -(i + j + 1)

        result = IndexCalculator.calculate_fraction(numerator, denominator)

        self.assertTrue(np.all(result == -5))

    def test_calculate_fraction_numerator_positive_denominator_zeros(self):
        numerator = np.ndarray(
            shape=self.shape,
            dtype="float64",
        )

        denominator = np.zeros(
            shape=self.shape,
            dtype="float64",
        )

        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                numerator[i, j] = i + j + 1

        result = IndexCalculator.calculate_fraction(numerator, denominator)

        self.assertTrue(np.all(result == 5))

    def test_calculate_fraction_numerator_zeros_denominator_zeros(self):
        numerator = np.zeros(
            shape=self.shape,
            dtype="float64",
        )

        denominator = np.zeros(
            shape=self.shape,
            dtype="float64",
        )

        result = IndexCalculator.calculate_fraction(numerator, denominator)

        self.assertTrue(np.all(np.isnan(result)))
