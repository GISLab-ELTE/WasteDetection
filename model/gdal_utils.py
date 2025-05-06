from osgeo import gdal
import numpy as np


def create_in_memory_dataset(data: np.ndarray, input_ds: gdal.Dataset, datatype=gdal.GDT_Int32) -> gdal.Dataset:
    """
    Creates an in-memory dataset.
    :param data: data that we want to add into the in-memory dataset
    :param input_ds: another dataset that will be used to obtain raster metadata, like projection
    :param datatype: the datatype that will be stored in the dataset.
    :returns: an in-memory dataset.
    """
    driver_mem = gdal.GetDriverByName("MEM")
    ds = driver_mem.Create("", input_ds.RasterXSize, input_ds.RasterYSize, 1, datatype)
    ds.SetProjection(input_ds.GetProjection())
    ds.SetGeoTransform(input_ds.GetGeoTransform())

    mask_band = ds.GetRasterBand(1)
    mask_band.WriteArray(data)
    mask_band.SetNoDataValue(0)

    return ds
