import unittest
import numpy as np
import model.persistence as persistence

from desktop_app.src.view_model import ViewModel


DEFAULT_RF_PATH = "desktop_app/clf/random_forest_model.sav"
CONFIG_FILE_NAME_DESKTOP_APP = "desktop_app/resources/config.sample.json"


class TestAddFiles(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_add_new_file(self) -> None:
        file_name = "NewFile1"

        self.add_files([file_name], lambda x: None)
        self.assertEqual(self._opened_files.count(file_name), 1)
        self.assertEqual(len(self._opened_files), 1)

    def test_add_the_same_file_twice(self):
        file_name = "NewFile1"

        self.add_files([file_name], lambda x: None)
        self.add_files([file_name], lambda x: None)
        self.assertEqual(self._opened_files.count(file_name), 1)
        self.assertEqual(len(self._opened_files), 1)

    def test_add_multiple_files(self):
        file_names = ["NewFile1", "NewFile2", "NewFile0", "NewFile1"]

        self.add_files(file_names, lambda x: None)
        self.assertEqual(self._opened_files.count(file_names[0]), 1)
        self.assertEqual(self._opened_files.count(file_names[1]), 1)
        self.assertEqual(self._opened_files.count(file_names[2]), 1)
        self.assertEqual(len(self._opened_files), 3)


class TestDeleteFiles(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_delete_file(self):
        self._opened_files += ["NewFile1", "NewFile2", "NewFile0", "NewFile4"]

        file_name = "NewFile0"

        self.delete_files([file_name])

        self.assertEqual(self._opened_files.count(file_name), 0)
        self.assertEqual(len(self._opened_files), 3)

    def test_delete_multiple_files(self):
        self._opened_files += ["NewFile1", "NewFile2", "NewFile0", "NewFile4"]

        file_names = ["NewFile0", "NewFile1"]

        self.delete_files(file_names)

        self.assertEqual(self._opened_files.count(file_names[0]), 0)
        self.assertEqual(self._opened_files.count(file_names[1]), 0)
        self.assertEqual(len(self._opened_files), 2)


class TestSaveTrainingInputFile(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_save_file(self):
        path = "D:/Desktop/test.tif"

        self.save_training_input_file(path)

        self.assertTrue(path in self._tag_ids.keys())
        self.assertEqual(len(self._tag_ids.keys()), 1)
        self.assertTrue(isinstance(self._tag_ids[path], dict))

    def test_save_same_file_twice(self):
        path = "D:/Desktop/test.tif"

        self.save_training_input_file(path)
        self.save_training_input_file(path)

        self.assertTrue(path in self._tag_ids.keys())
        self.assertEqual(len(self._tag_ids.keys()), 1)
        self.assertTrue(isinstance(self._tag_ids[path], dict))


class TestSavePointOnCanvas(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_save_point(self):
        tag_id = 42

        self.save_point_on_canvas(tag_id)

        self.assertEqual(self._point_tag_ids.count(tag_id), 1)
        self.assertEqual(len(self._point_tag_ids), 1)


class TestSaveNewC(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_save_class(self):
        training_file = "D:/Desktop/test.tif"
        c_id = 1
        c_name = "Garbage"
        color = "#ffffff"

        self.save_training_input_file(training_file)
        self.save_new_c(training_file, c_id, c_name, color)

        self.assertTrue(training_file in self._tag_ids.keys())
        self.assertTrue(c_id in self._tag_ids[training_file].keys())
        self.assertTrue(self._tag_ids[training_file][c_id] == [c_name, color, []])
        self.assertEqual(len(self._tag_ids.keys()), 1)
        self.assertEqual(len(self._tag_ids[training_file].keys()), 1)

    def test_save_multiple_classes(self):
        training_file_1 = "D:/Desktop/test_1.tif"
        c_id_1 = 1
        c_name_1 = "Garbage"
        color_1 = "#ffffff"

        training_file_2 = "D:/Desktop/test_2.tif"
        c_id_2 = 2
        c_name_2 = "Water"
        color_2 = "#000000"

        training_file_3 = "D:/Desktop/test_3.tif"
        c_id_3 = 3
        c_name_3 = "Forest"
        color_3 = "#cccccc"

        self.save_training_input_file(training_file_1)
        self.save_training_input_file(training_file_2)
        self.save_training_input_file(training_file_3)

        self.save_new_c(training_file_1, c_id_1, c_name_1, color_1)
        self.save_new_c(training_file_2, c_id_2, c_name_2, color_2)
        self.save_new_c(training_file_3, c_id_3, c_name_3, color_3)

        self.assertTrue(
            all(
                file in self._tag_ids.keys()
                for file in [training_file_1, training_file_2, training_file_3]
            )
        )

        self.assertTrue(c_id_1 in self._tag_ids[training_file_1].keys())
        self.assertTrue(c_id_2 in self._tag_ids[training_file_2].keys())
        self.assertTrue(c_id_3 in self._tag_ids[training_file_3].keys())

        self.assertTrue(
            self._tag_ids[training_file_1][c_id_1] == [c_name_1, color_1, []]
        )
        self.assertTrue(
            self._tag_ids[training_file_2][c_id_2] == [c_name_2, color_2, []]
        )
        self.assertTrue(
            self._tag_ids[training_file_3][c_id_3] == [c_name_3, color_3, []]
        )

        self.assertEqual(len(self._tag_ids.keys()), 3)
        self.assertEqual(len(self._tag_ids[training_file_1].keys()), 1)
        self.assertEqual(len(self._tag_ids[training_file_2].keys()), 1)
        self.assertEqual(len(self._tag_ids[training_file_3].keys()), 1)

        self.save_new_c(training_file_1, c_id_3, c_name_3, color_3)
        self.save_new_c(training_file_1, c_id_3, c_name_3, color_3)
        self.assertTrue(c_id_3 in self._tag_ids[training_file_1].keys())
        self.assertEqual(len(self._tag_ids[training_file_1].keys()), 2)


class TestDeleteC(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_delete_class(self):
        training_file_1 = "D:/Desktop/test_1.tif"

        c_id_1 = 1
        c_name_1 = "Garbage"
        color_1 = "#ffffff"

        c_id_2 = 2
        c_name_2 = "Water"
        color_2 = "#000000"

        c_id_3 = 3
        c_name_3 = "Forest"
        color_3 = "#cccccc"

        self.save_training_input_file(training_file_1)

        self.save_new_c(training_file_1, c_id_1, c_name_1, color_1)
        self.save_new_c(training_file_1, c_id_2, c_name_2, color_2)
        self.save_new_c(training_file_1, c_id_3, c_name_3, color_3)

        for i in range(6):
            self.save_tag_id(training_file_1, c_id_1, c_name_1, color_1, i)

        self.assertTrue(c_id_1 in self._tag_ids[training_file_1].keys())
        self.assertEqual(len(self._tag_ids[training_file_1].keys()), 3)

        deleted_tag_ids = self.delete_c(training_file_1, c_id_1)

        self.assertEqual(deleted_tag_ids, [0, 1, 2, 3, 4, 5])

        self.assertFalse(c_id_1 in self._tag_ids[training_file_1].keys())
        self.assertEqual(len(self._tag_ids[training_file_1].keys()), 2)

        deleted_tag_ids = self.delete_c(training_file_1, c_id_2)

        self.assertEqual(deleted_tag_ids, [])
        self.assertFalse(c_id_2 in self._tag_ids[training_file_1].keys())
        self.assertEqual(len(self._tag_ids[training_file_1].keys()), 1)


class TestDeleteTagId(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_delete_tag_ids(self):
        training_file_1 = "D:/Desktop/test_1.tif"

        c_id_1 = 1
        c_name_1 = "Garbage"
        color_1 = "#ffffff"

        c_id_2 = 2
        c_name_2 = "Water"
        color_2 = "#000000"

        self.save_training_input_file(training_file_1)

        self.save_new_c(training_file_1, c_id_1, c_name_1, color_1)
        self.save_new_c(training_file_1, c_id_2, c_name_2, color_2)

        self.assertEqual(len(self._tag_ids[training_file_1].keys()), 2)

        for i in range(6):
            self.save_tag_id(training_file_1, c_id_1, c_name_1, color_1, i)

        for i in range(1, 4):
            self.delete_tag_id(training_file_1, i)

        self.assertEqual(len(self._tag_ids[training_file_1][c_id_1][2]), 3)
        self.assertEqual(self._tag_ids[training_file_1][c_id_1][2], [0, 4, 5])
        self.assertEqual(len(self._tag_ids[training_file_1][c_id_2][2]), 0)


class TestSaveTagId(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_save_tag_ids(self):
        training_file_1 = "D:/Desktop/test_1.tif"
        c_id_1 = 1
        c_name_1 = "Garbage"
        color_1 = "#ffffff"

        self.save_training_input_file(training_file_1)
        self.save_new_c(training_file_1, c_id_1, c_name_1, color_1)

        for i in range(6):
            self.save_tag_id(training_file_1, c_id_1, c_name_1, color_1, i)

        self.assertEqual(self._tag_ids[training_file_1][c_id_1][2], [0, 1, 2, 3, 4, 5])


class TestSaveTagIdCoords(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_save_tag_id_coord(self):
        training_file_1 = "D:/Desktop/test_1.tif"
        c_id_1 = 1
        c_name_1 = "Garbage"
        coords = [[(1, 2), (1, 3), (4, 2), (6, 9)], [0, 0]]
        bbox_coords = [(1, 2, 3, 4), (0, 0, 0, 0)]

        self.save_tag_id_coords(training_file_1, c_id_1, c_name_1, coords, bbox_coords)

        self.assertTrue(training_file_1 in self._tag_id_coords.keys())
        self.assertTrue(c_id_1 in self._tag_id_coords[training_file_1].keys())
        self.assertEqual(len(self._tag_id_coords.keys()), 1)
        self.assertEqual(len(self._tag_id_coords[training_file_1].keys()), 1)
        self.assertEqual(self._tag_id_coords[training_file_1][c_id_1][1], coords)
        self.assertEqual(self._tag_id_coords[training_file_1][c_id_1][2], bbox_coords)


class TestDeletePoints(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_delete_points(self):
        for i in range(42):
            self.save_point_on_canvas(i)

        deleted_points = self.delete_points()

        self.assertEqual(deleted_points, list(range(42)))
        self.assertEqual(len(self._point_tag_ids), 0)


class TestPlacePolygonOnCanvas(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_not_enough_points(self):
        self.save_point_on_canvas(33)
        self.save_point_on_canvas(12)

        tag_ids = self.place_polygon_on_canvas()

        self.assertEqual(tag_ids, [])
        self.assertEqual(len(self._point_tag_ids), 2)

    def test_enough_points(self):
        for i in range(100):
            self.save_point_on_canvas(i)

        tag_ids = self.place_polygon_on_canvas()

        self.assertEqual(tag_ids, list(range(100)))
        self.assertEqual(len(self._point_tag_ids), 0)


class TestCreateUsableTrainingData(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_no_usable_one_file(self):
        training_file_1 = "D:/Desktop/test_1.tif"
        c_ids = [1, 2, 3]

        test_dict = dict()
        test_dict[training_file_1] = dict()
        for c_id in c_ids:
            test_dict[training_file_1][c_id] = ["name", [], []]

        self._tag_id_coords = test_dict
        usable_training_data, enough_data = self.create_usable_training_data()

        self.assertFalse(enough_data)
        self.assertEqual(usable_training_data, {})

    def test_no_usable_more_files(self):
        training_files = [
            "D:/Desktop/test_1.tif",
            "D:/Desktop/test_2.tif",
            "D:/Desktop/test_3.tif",
        ]
        c_ids = [1, 2, 3]
        test_dict = dict()

        for training_file in training_files:
            test_dict[training_file] = dict()

        for i in range(len(training_files)):
            for c_id in c_ids[: i + 1]:
                test_dict[training_files[i]][c_id] = ["name", [], []]

        self.assertEqual(len(test_dict.keys()), 3)
        for i in range(len(training_files)):
            self.assertEqual(len(test_dict[training_files[i]].keys()), i + 1)

        self._tag_id_coords = test_dict
        usable_training_data, enough_data = self.create_usable_training_data()

        self.assertFalse(enough_data)
        self.assertEqual(usable_training_data, {})

    def test_one_usable_one_file(self):
        training_file_1 = "D:/Desktop/test_1.tif"
        c_ids = [1, 2, 3]

        test_dict = dict()
        test_dict[training_file_1] = dict()
        for c_id in c_ids:
            if c_id == 2:
                test_dict[training_file_1][c_id] = [
                    "name",
                    [[1.1, 2.2, 3.3, 4.4]],
                    [(1, 2, 3, 4)],
                ]
            else:
                test_dict[training_file_1][c_id] = ["name", [], []]

        self._tag_id_coords = test_dict
        usable_training_data, enough_data = self.create_usable_training_data()

        self.assertFalse(enough_data)
        self.assertEqual(
            usable_training_data,
            {training_file_1: {2: ["name", [[1.1, 2.2, 3.3, 4.4]], [(1, 2, 3, 4)]]}},
        )

    def test_one_usable_more_files(self):
        training_files = [
            "D:/Desktop/test_1.tif",
            "D:/Desktop/test_2.tif",
            "D:/Desktop/test_3.tif",
        ]
        c_ids = [1, 2, 3]
        test_dict = dict()

        for training_file in training_files:
            test_dict[training_file] = dict()

        self.assertEqual(len(test_dict), 3)

        for i in range(len(training_files)):
            for c_id in c_ids[: i + 1]:
                if i == 2 and c_id == 3:
                    test_dict[training_files[i]][c_id] = [
                        "name",
                        [[1.1, 2.2, 3.3, 4.4]],
                        [(1, 2, 3, 4)],
                    ]
                else:
                    test_dict[training_files[i]][c_id] = ["name", [], []]

        self._tag_id_coords = test_dict
        usable_training_data, enough_data = self.create_usable_training_data()

        self.assertFalse(enough_data)
        self.assertEqual(
            usable_training_data,
            {training_files[2]: {3: ["name", [[1.1, 2.2, 3.3, 4.4]], [(1, 2, 3, 4)]]}},
        )

    def test_more_usable_one_file(self):
        training_file_1 = "D:/Desktop/test_1.tif"
        c_ids = [1, 2, 3]
        test_dict = dict()
        test_dict[training_file_1] = dict()

        for c_id in c_ids:
            test_dict[training_file_1][c_id] = [
                "name",
                [[1.1, 2.2, 3.3, 4.4]],
                [(1, 2, 3, 4)],
            ]

        self._tag_id_coords = test_dict
        usable_training_data, enough_data = self.create_usable_training_data()

        self.assertTrue(enough_data)
        self.assertEqual(
            usable_training_data,
            {
                training_file_1: {
                    1: ["name", [[1.1, 2.2, 3.3, 4.4]], [(1, 2, 3, 4)]],
                    2: ["name", [[1.1, 2.2, 3.3, 4.4]], [(1, 2, 3, 4)]],
                    3: ["name", [[1.1, 2.2, 3.3, 4.4]], [(1, 2, 3, 4)]],
                }
            },
        )

    def test_more_usable_more_files(self):
        training_file_1 = "D:/Desktop/test_1.tif"
        training_file_2 = "D:/Desktop/test_2.tif"
        c_ids = [1, 2, 3]
        test_dict = dict()
        test_dict[training_file_1] = dict()
        test_dict[training_file_2] = dict()

        for training_file in [training_file_1, training_file_2]:
            for c_id in c_ids:
                test_dict[training_file][c_id] = [
                    "name",
                    [[1.1, 2.2, 3.3, 4.4]],
                    [(1, 2, 3, 4)],
                ]

        self._tag_id_coords = test_dict
        usable_training_data, enough_data = self.create_usable_training_data()

        self.assertTrue(enough_data)
        self.assertEqual(usable_training_data, test_dict)


class TestGetCoordsInsidePolygon(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

    def test_convex_polygon(self):
        polygon_coords = [1.0, 1.0, 2.0, 5.0, 4.0, 3.0, 3.0, 1.0]
        bbox_coords = (1, 1, 4, 5)

        result = self.get_coords_inside_polygon(polygon_coords, bbox_coords)

        expected = [(2, 2), (3, 2), (2, 3), (3, 3), (2, 4)]

        self.assertEqual(len(result), len(expected))
        for value in expected:
            self.assertTrue(value in result)

    def test_concave_polygon(self):
        polygon_coords = [2.0, 7.0, 8.0, 1.0, 2.0, 3.0, 10.0, 9.0]
        bbox_coords = (2, 1, 10, 9)

        result = self.get_coords_inside_polygon(polygon_coords, bbox_coords)

        expected = [
            (6, 2),
            (5, 3),
            (4, 3),
            (3, 3),
            (4, 4),
            (4, 6),
            (5, 6),
            (3, 7),
            (4, 7),
            (5, 7),
            (6, 7),
            (7, 7),
            (7, 8),
            (8, 8),
        ]

        self.assertEqual(len(result), len(expected))
        for value in expected:
            self.assertTrue(value in result)


class TestCalculateIndex(unittest.TestCase, ViewModel):
    def setUp(self) -> None:
        ViewModel.__init__(
            self, persistence=persistence.Persistence(CONFIG_FILE_NAME_DESKTOP_APP)
        )

        self.shape = (3, 3)

    def test_all_nan(self):
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

        result = self.calculate_index(numerator, denominator)

        self.assertTrue(np.array_equal(result, numerator, equal_nan=True))
        self.assertTrue(np.array_equal(result, denominator, equal_nan=True))

    def test_all_not_nan(self):
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

        result = self.calculate_index(numerator, denominator)

        self.assertTrue(np.all(result == 1))

    def test_numerator_negative_denominator_zeros(self):
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

        result = self.calculate_index(numerator, denominator)

        self.assertTrue(np.all(result == -5))

    def test_numerator_positive_denominator_zeros(self):
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

        result = self.calculate_index(numerator, denominator)

        self.assertTrue(np.all(result == 5))

    def test_numerator_zeros_denominator_zeros(self):
        numerator = np.zeros(
            shape=self.shape,
            dtype="float64",
        )

        denominator = np.zeros(
            shape=self.shape,
            dtype="float64",
        )

        result = self.calculate_index(numerator, denominator)

        self.assertTrue(np.all(np.isnan(result)))


if __name__ == "__main__":
    unittest.main()
