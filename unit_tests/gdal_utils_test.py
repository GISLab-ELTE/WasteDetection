import unittest
import numpy as np
from osgeo import gdal

import model.gdal_utils as gdal_utils


class TestGdalUtils(unittest.TestCase):
    def test_create_in_memory_dataset(self):
        # arrange
        driver_mem = gdal.GetDriverByName("MEM")
        ds = driver_mem.Create("", 3, 2, 1, gdal.GDT_Int32)
        srs = gdal.osr.SpatialReference()
        srs.SetUTM(11, 1)
        srs.SetWellKnownGeogCS("NAD27")
        ds.SetProjection(srs.ExportToWkt())
        ds.SetGeoTransform([444720, 30, 0, 3751320, 0, -30])

        expected_mask = np.asarray([[True, False, True], [True, True, False]])

        # act
        mask_ds = gdal_utils.create_in_memory_dataset(expected_mask, ds)

        # assert
        self.assertEqual(mask_ds.GetProjection(), ds.GetProjection(), "Projections didnt match")
        self.assertEqual(mask_ds.GetGeoTransform(), ds.GetGeoTransform(), "GeoTransforms didnt match")
        self.assertEqual(mask_ds.RasterXSize, ds.RasterXSize, "RasterXSize didnt match")
        self.assertEqual(mask_ds.RasterYSize, ds.RasterYSize, "RasterYSize didnt match")
        self.assertEqual(mask_ds.RasterCount, 1, "Raster count was not 1")
        self.assertTrue(np.all(mask_ds.ReadAsArray() == expected_mask), "mask was not equal with expected mask")
