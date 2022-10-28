import rasterio
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from osgeo import gdal
from matplotlib import cm
from model.exceptions import *
from PIL import Image, ImageTk
from typing import Tuple, Union, List
from auto_scrollbar import AutoScrollbar
from matplotlib.colors import ListedColormap


# constants
MAX_PIXEL_COUNT = 40000000


class ZoomCanvas(ttk.Frame):
    """
    A canvas with zoom-in, zoom-out and move functions.
    It is for displaying images.

    """

    def __init__(self, mainframe):
        """
        Constructor of ZoomCanvas class.

        :param mainframe: parent widget
        """

        super(ZoomCanvas, self).__init__(master=mainframe)

        self._image = None
        self._img_id = None

        self._initialize_components()
        self._configure_components()
        self._place_components()
        self._initialize_data_members()

    # Class properties
    @property
    def canvas(self) -> tk.Canvas:
        return self._canvas

    # Non-static public methods
    def is_point_or_polygon(self, tag_id: int) -> bool:
        """
        Decides whether the given tag id belongs to a polygon/point or not.

        :param tag_id: tag id of a shape
        :return: True or False
        """

        return (tag_id in self._canvas.find_all()) and tag_id != self._img_id and tag_id != self._fix_point

    def open_image(self, input_path: str, image_type: str, satellite_rgb: List[int],
                   color_map: ListedColormap = cm.get_cmap("viridis")) -> None:
        """
        Loads an image with the given color map for later use.

        :param input_path: path of the image to be loaded
        :param image_type: "rgb", "classified" or "heatmap"
        :param satellite_rgb: indices of RGB bands on satellite image
        :param color_map: color map
        :return: None
        :raise ImageTypeException: if the image_type parameter is wrong
        :raise PictureDoesNotExistException: if the image to be opened does not exist
        :raise TooLargeImageException: if the image to be opened exceeds the supported maximum pixel count
        :raise NotEnoughBandsException: if the image to be opened does not have enough bands
        """

        if len(input_path) == 0:
            return

        if image_type.lower() not in ["rgb", "classified", "heatmap"]:
            raise ImageTypeException(image_type.lower())

        if image_type.lower() == "rgb":
            try:
                dataset = gdal.Open(input_path, gdal.GA_ReadOnly)

                if dataset is None:
                    raise PictureDoesNotExistException(input_path)

                rows = dataset.RasterYSize
                cols = dataset.RasterXSize

                if rows * cols > MAX_PIXEL_COUNT:
                    raise TooLargeImageException(rows * cols, MAX_PIXEL_COUNT, input_path)

                if dataset.RasterCount < 3:
                    raise NotEnoughBandsException(dataset.RasterCount, 3, input_path)

                if dataset.RasterCount < max(satellite_rgb):
                    raise NotEnoughBandsException(dataset.RasterCount, max(satellite_rgb), input_path)

                band1 = dataset.GetRasterBand(satellite_rgb[2])  # Blue channel
                band2 = dataset.GetRasterBand(satellite_rgb[1])  # Green channel
                band3 = dataset.GetRasterBand(satellite_rgb[0])  # Red channel

                blue = band1.ReadAsArray()
                green = band2.ReadAsArray()
                red = band3.ReadAsArray()

                blue_n = ((blue.astype(np.float64) - blue.min()) * (255 / blue.max())).astype(np.uint8)
                green_n = ((green.astype(np.float64) - green.min()) * (255 / green.max())).astype(np.uint8)
                red_n = ((red.astype(np.float64) - red.min()) * (255 / red.max())).astype(np.uint8)

                dataset = np.dstack((red_n, green_n, blue_n))

                self._image = Image.fromarray(dataset, "RGB")
            except Exception:
                raise
            finally:
                del dataset
        elif image_type.lower() in ["classified", "heatmap"]:
            try:
                with rasterio.open(input_path, "r") as dataset:
                    if dataset.count != 1:
                        raise NotEnoughBandsException(dataset.count, 1, input_path)

                    if dataset.width * dataset.height > MAX_PIXEL_COUNT:
                        raise TooLargeImageException(dataset.width * dataset.height, MAX_PIXEL_COUNT, input_path)

                    dataset = dataset.read(1)

                    unique_values = np.unique(dataset)

                    for i in range(len(unique_values)):
                        dataset = np.where(dataset == unique_values[i], i, dataset)

                    if np.nanmax(dataset) != 0:
                        dataset /= np.nanmax(dataset)

                    self._image = Image.fromarray(np.uint8(color_map(dataset)*255))
            except NotEnoughBandsException:
                raise
            except TooLargeImageException:
                raise
            except rasterio.RasterioIOError:
                raise PictureDoesNotExistException(input_path)

        self._show_image()

    def delete_image(self) -> None:
        """
        Deletes image from canvas.

        :return: None
        """

        if self._img_id:
            self._canvas.delete(self._img_id)
            self._img_id = None
            self._canvas.imagetk = None  # delete previous image from the canvas
            self._image = None
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def hide_shape(self, tag_id: int) -> None:
        """
        Hides a shape with the given tag id from the canvas.

        :param tag_id: tag id of a shape
        :return: None
        """

        self.canvas.itemconfigure(tag_id, state="hidden")

    def show_shape(self, tag_id: int) -> None:
        """
        Displays a shape with the given tag id on the canvas.

        :param tag_id: tag id of a shape
        :return: None
        """

        self.canvas.itemconfigure(tag_id, state="normal")

    def place_point_on_canvas(self, event) -> Union[int, None]:
        """
        Draws an oval shape (point) on the canvas.

        :param event: event parameter
        :return: tag id of the drawn shape, or None if it could not be placed
        """

        if self._image is None:
            return

        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)

        if not (5 <= x < self._new_size[0] - 5) or not (5 <= y < self._new_size[1] - 5):
            return

        size = self._img_scale

        x1, y1 = (x - 2 * size), (y - 2 * size)
        x2, y2 = (x + 2 * size), (y + 2 * size)

        tag_id = self._canvas.create_oval(x1, y1, x2, y2, fill="red", state="normal")

        return tag_id

    def get_coords_of_point(self, tag_id: int) -> Tuple[float, float]:
        """
        Calculates the coordinates of a point on canvas.

        :param tag_id: tag id of a shape
        :return: x, y coordinates
        """

        coords = self._canvas.bbox(tag_id)
        size = self._img_scale

        x2, y2 = coords[2:]

        center_x, center_y = (x2 - 2 * size), (y2 - 2 * size)

        return center_x, center_y

    def delete_points_from_canvas(self, tag_ids: List[int]) -> None:
        """
        Deletes the specified oval shape (point) from the canvas.

        :param tag_ids: tag id of the oval shape
        :return: None
        """

        for tag_id in tag_ids:
            self._canvas.delete(tag_id)

    def place_polygon_on_canvas(self, coords: List[Tuple[float, float]], color: str) -> int:
        """
        Draws a polygon on the canvas.

        :param coords: coordinates of the polygon's vertices
        :param color: color of the polygon
        :return: tag id of the drawn polygon
        """

        reshape_coords = [j for i in coords for j in i]
        tag_id = self._canvas.create_polygon(reshape_coords, outline="black", fill=color, state="normal")
        self._polygons.append(tag_id)
        return tag_id

    def delete_polygon_from_canvas(self, tag_ids: List[int]) -> None:
        """
        Deletes the specified polygon/polygons from the canvas.

        :param tag_ids: tag ids of the polygons
        :return: None
        """

        for tag_id in tag_ids:
            self._canvas.delete(tag_id)

    def move_from(self, event) -> None:
        """
        Records the previous coordinates for scrolling with the mouse.

        :param event: event parameter
        :return: None
        """

        self._canvas.scan_mark(event.x, event.y)

    def move_to(self, event) -> None:
        """
        Drags (moves) canvas to the new position.

        :param event: event parameter
        :return: None
        """

        self._canvas.scan_dragto(event.x, event.y, gain=1)

    def wheel(self, event) -> None:
        """
        Zooms with mouse wheel.

        :param event: event parameter
        :return: None
        """

        if self._image is None:
            return

        scale = 1.0

        # Respond to Windows (event.delta) wheel event
        if event.delta == -120:
            scale *= self._delta
            if self._img_scale * self._delta < 0.10:
                return
            self._img_scale *= self._delta
        if event.delta == 120:
            scale /= self._delta
            width, height = self._image.size
            new_img_scale = self._img_scale / self._delta
            new_size = int(new_img_scale * width) * int(new_img_scale * height)
            if new_size > MAX_PIXEL_COUNT:
                return
            self._img_scale /= self._delta

        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        self._rescale(x, y, scale)
        self._show_image()

    def rescale_to_original_size(self) -> None:
        """
        Rescales the canvas to its original size.

        :return: None
        """

        if self._img_scale == 1.0:
            return

        scale = 1.0
        while self._img_scale > 1.0:
            scale *= self._delta
            self._img_scale *= self._delta
        while self._img_scale < 1.0:
            scale /= self._delta
            self._img_scale /= self._delta

        x = self._canvas.canvasx(0)
        y = self._canvas.canvasy(0)
        self._rescale(x, y, scale)
        self._show_image()

    # Non-static protected methods
    def _rescale(self, x: float, y: float, scale: float) -> None:
        """
        Rescales all canvas objects.

        :param x: x coordinate of the origin
        :param y: y coordinate of the origin
        :param scale: the scaling value
        :return: None
        """

        self._canvas.scale("all", x, y, scale, scale)
        offset = self._canvas.coords([self._fix_point])
        self._canvas.move("all", offset[0] * -1, offset[1] * -1)

    def _show_image(self) -> None:
        """
        Displays the image on the canvas.

        :return: None
        """

        if not self._image:
            return

        if self._img_id:
            self._canvas.delete(self._img_id)
            self._img_id = None
            self._canvas.imagetk = None  # delete previous image from the canvas

        width, height = self._image.size
        self._new_size = int(self._img_scale * width), int(self._img_scale * height)

        imagetk = ImageTk.PhotoImage(self._image.resize(self._new_size))

        self._img_id = self._canvas.create_image(self._canvas.coords([self._fix_point]), anchor="nw", image=imagetk)
        self._canvas.lower(self._img_id)  # set it into background
        self._canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _initialize_components(self) -> None:
        """
        Initializes the visual components.

        :return: None
        """

        self._vertical_sb = AutoScrollbar(master=self.master, orient="vertical")
        self._horizontal_sb = AutoScrollbar(master=self.master, orient="horizontal")
        self._canvas = tk.Canvas(master=self.master)

    def _configure_components(self) -> None:
        """
        Configures the visual components.

        :return: None
        """

        self._canvas.configure(
            highlightthickness=0,
            xscrollcommand=self._horizontal_sb.set,
            yscrollcommand=self._vertical_sb.set
        )

        self._vertical_sb.configure(command=self._canvas.yview)
        self._horizontal_sb.configure(command=self._canvas.xview)

        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

    def _place_components(self) -> None:
        """
        Places the visual components on the window.

        :return: None
        """

        self._vertical_sb.grid(row=0, column=1, sticky="ns")
        self._horizontal_sb.grid(row=1, column=0, sticky="ew")
        self._canvas.grid(row=0, column=0, sticky="nsew")

    def _initialize_data_members(self) -> None:
        """
        Initializes the data members.

        :return: None
        """

        self._polygons = list()

        self._new_size = None
        self._img_scale = 1.0
        self._delta = 0.9

        self._fix_point = self._canvas.create_text(0, 0, anchor='nw', text="", fill="white")
