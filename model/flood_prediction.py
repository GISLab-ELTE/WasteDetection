import math

import geopandas as gpd
import pyproj
import rasterio
from shapely.geometry import Point


class FloodPrediction:
    """
    A class containing flood-related utility methods.
    """

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points on the Earth.
        """
        R = 6371000  # radius in meters
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def get_elevation_from_dem(dem_path: str, point: Point, point_crs: str, dem_crs: str) -> float:
        """
        Returns the elevation for a given point from a DEM file.
        """
        transformer = pyproj.Transformer.from_crs(point_crs, dem_crs, always_xy=True)
        x, y = transformer.transform(point.x, point.y)
        with rasterio.open(dem_path) as dem:
            row, col = dem.index(x, y)
            return float(dem.read(1)[row, col])

    @staticmethod
    def check_flood_zone(point: Point, flood_zones: dict, point_crs: str) -> list:
        """
        Check to which flood zones a point belongs.
        :param point: Shapely point.
        :param flood_zones: Dictionary of flood zone names and corresponding shapefile paths.
        :param point_crs: The CRS to use for filtering.
        :return: List of zone names or ["no flood zone"]
        """
        res = []
        for zone_name, shp_path in flood_zones.items():
            gdf = gpd.read_file(shp_path)
            if gdf.crs != point_crs:
                gdf = gdf.to_crs(point_crs)
            if gdf.contains(point).any():
                res.append(zone_name)
        return res if res else ["no flood zone"]
