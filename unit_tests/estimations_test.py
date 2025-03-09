import unittest
import numpy as np
import model.estimations as estimations
from model.treshold import Treshold


class TestEstimations(unittest.TestCase):
    def test_create_heatmap_with_no_tresholds_returns_heatmap_with_zeroes(self):
        # arrange
        probabilities = np.linspace(0, 1, num=10)
        tresholds = []

        # act
        heatmap = estimations.create_heatmap(probabilities, tresholds)

        # assert
        self.assertTrue(np.all(heatmap == 0), "Heatmap should have all zeroes!")
        self.assertEqual(probabilities.shape, heatmap.shape)

    def test_create_heatmap_keeps_shape_of_probabilities_array(self):
        # arrange
        probabilities = np.linspace(0, 1, num=10).reshape(2, 5)
        tresholds = []

        # act
        heatmap = estimations.create_heatmap(probabilities, tresholds)

        # assert
        self.assertEqual(probabilities.shape, heatmap.shape)

    def test_create_heatmap_with_one_treshold_returns_correct_heatmap(self):
        # arrange
        probabilities = np.linspace(0.1, 1, num=10)
        expected = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
        tresholds = [Treshold(0.5, 1)]

        # act
        heatmap = estimations.create_heatmap(probabilities, tresholds)

        # assert
        self.assertTrue(np.all(expected == heatmap), "Heatmap does not have expected values!")

    def test_create_heatmap_with_three_tresholds_returns_correct_heatmap(self):
        # arrange
        probabilities = np.linspace(0.1, 1, num=10)
        expected = [0, 0, 1, 1, 1, 2, 2, 2, 3, 3]
        tresholds = [
            Treshold(0.3, 1),
            Treshold(0.6, 2),
            Treshold(0.9, 3),
        ]

        # act
        heatmap = estimations.create_heatmap(probabilities, tresholds)

        # assert
        self.assertTrue(np.all(expected == heatmap), "Heatmap does not have expected values!")
