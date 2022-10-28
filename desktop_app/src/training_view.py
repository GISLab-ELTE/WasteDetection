import tkinter as tk
import ttkbootstrap as ttk

from zoom_canvas import ZoomCanvas
from auto_scrollbar import AutoScrollbar
from typing import List, Tuple, Union
from ttkbootstrap.constants import *


SIZE = "1600x900"


class TrainingView(ttk.Toplevel):
    """
    A window for training Random Forest with training images.

    """

    def __init__(self, master: ttk.Window):
        """
        The constructor of the TrainingView class.

        :param master: the master/parent window of this class
        """

        super(TrainingView, self).__init__(master=master)

        self._configure_window()
        self._initialize_components()
        self._configure_components()
        self._style_components()
        self._place_components()

        self._zoom_canvas = ZoomCanvas(self._canvas_lf)

        self.withdraw()

    # Class properties
    @property
    def back_btn(self) -> ttk.Button:
        return self._back_btn

    @property
    def open_input_img_btn(self) -> ttk.Button:
        return self._open_input_img_btn

    @property
    def delete_input_img_btn(self) -> ttk.Button:
        return self._delete_input_img_btn

    @property
    def opened_files_lb(self) -> tk.Listbox:
        return self._opened_files_lb

    @property
    def add_btn(self) -> ttk.Button:
        return self._add_btn

    @property
    def delete_btn(self) -> ttk.Button:
        return self._delete_btn

    @property
    def mc_spinbox(self) -> ttk.Spinbox:
        return self._mc_spinbox

    @property
    def mc_input(self) -> ttk.Entry:
        return self._mc_input

    @property
    def color_btn(self) -> ttk.Button:
        return self._color_btn

    @property
    def treeview(self) -> ttk.Treeview:
        return self._treeview

    @property
    def training_btn(self) -> ttk.Button:
        return self._training_btn

    @property
    def process_pb(self) -> ttk.Progressbar:
        return self._process_pb

    @property
    def zoom_canvas(self) -> ZoomCanvas:
        return self._zoom_canvas

    # Non-static public methods
    def show(self) -> None:
        """
        Displays the window if is withdrawn.

        :return: None
        """

        self.update()
        self.deiconify()

    def add_file_to_listbox(self, file: str) -> None:
        """
        Inserts file into listbox.

        :param file: path of the file to be inserted
        :return: None
        """

        self._opened_files_lb.insert(END, file)

    def remove_file_from_listbox(self, file_index: int) -> None:
        """
        Removes file from listbox.

        :param file_index: the index of the file to be removed
        :return: None
        """

        self._opened_files_lb.delete(file_index)

    def get_curselection_value_listbox(self) -> Union[str, None]:
        """
        Returns the value of the selected item in the listbox.

        :return: the value of the selected item if selected, None otherwise
        """

        selected_index = self._opened_files_lb.curselection()

        if len(selected_index) > 0:
            selected_value = self._opened_files_lb.get(selected_index)
            return selected_value

        return None

    def get_mc_id(self) -> int:
        """
        Returns the value in the Class ID Spinbox.

        :return: Class ID value
        """

        return int(self._mc_spinbox.get())

    def get_mc_name(self) -> str:
        """
        Return the value in the Class Name Entry.

        :return: Class NAME value
        """

        return self._mc_input.get()

    def get_mc_color(self) -> str:
        """
        Returns the background color of the Color Button.

        :return: background color
        """

        return self._color_btn.cget("bg")

    def set_mc_id(self, value: int) -> None:
        """
        Sets the value in the Class ID Spinbox.

        :param value: the value to be set
        :return: None
        """

        self._mc_spinbox.set(value)

    def set_mc_name(self, value: str) -> None:
        """
        Sets the value in the Class Name Entry.

        :param value: the value to be set
        :return: None
        """

        self._mc_input.delete(0, END)
        self._mc_input.insert(0, value)

    def set_color_btn_bg(self, value: str) -> None:
        """
        Sets the background color of the Color Button.

        :param value: the value to be set
        :return: None
        """

        self._color_btn.configure(bg=value, activebackground=value)

    def get_selection_treeview(self) -> Tuple[str, ...]:
        """
        Returns the item selected in Treeview.

        :return: tuple of selected ids
        """

        return self._treeview.selection()

    def insert_into_treeview(self, parent: str, index: int,
                             iid: Union[int, None], values: Tuple[str, Union[int, str], Union[int, str]]) -> None:
        """
        Insert new values into Treeview.

        :param parent: parent id
        :param index: child index among parent's children
        :param iid: individual id
        :param values: the value to be inserted
        :return: None
        """

        self._treeview.insert(parent=parent, index=index, iid=iid, values=values, open=True)

    def clear_treeview(self) -> None:
        """
        Deletes all items from Treeview.

        :return: None
        """

        for i in self._treeview.get_children():
            self._treeview.delete(i)

    def place_polygon_on_canvas(self, coords: List[Tuple[float, float]]) -> Tuple[int, str, str, int]:
        """
        Places a polygon with the given coordinates and color onto canvas.

        :param coords: coordinates of the polygon's vertices
        :return: Class ID, Class NAME, COLOR, TAG ID
        """

        color = self._color_btn.cget("bg")
        tag_id = self._zoom_canvas.place_polygon_on_canvas(coords, color)
        mc_id = self.get_mc_id()
        mc_name = self.get_mc_name()
        return mc_id, mc_name, color, tag_id

    def get_coords_of_tag_id_on_canvas(self, tags: List[int]) -> Tuple[List[List[float]], List[Tuple[int, ...]]]:
        """
        Calculates coordinates and bounding boxes of given tag ids.

        :param tags: list of tag ids
        :return: coordinates and bounding boxes
        """

        coords = list()
        bbox_coords = list()

        for tag in tags:
            coords.append(self._zoom_canvas.canvas.coords([tag]))
            bbox_coords.append(self._zoom_canvas.canvas.bbox(tag))

        return coords, bbox_coords

    def get_coords_of_points_on_canvas(self, tag_ids: List[int]) -> List[Tuple[float, float]]:
        """
        Gets coordinates of points on canvas.

        :param tag_ids: list of tag ids
        :return: list coordinates
        """

        coords = list()
        for tag_id in tag_ids:
            x, y = self._zoom_canvas.get_coords_of_point(tag_id)
            coords.append((x, y))
        return coords

    def rescale_to_original_size(self) -> None:
        """
        Rescales the canvas to its original size.

        :return: None
        """

        self._zoom_canvas.rescale_to_original_size()

    # Non-static protected methods
    def _configure_window(self) -> None:
        """
        Configures the window.

        :return: None
        """

        self.title("Train Random Forest Classifier")
        self.resizable(width=False, height=False)
        self.geometry(SIZE)
        self.place_window_center()

    def _initialize_components(self) -> None:
        """
        Initializes the visual components.

        :return: None
        """

        # initialize user action components
        self._action_lf = ttk.Labelframe(master=self)
        self._back_btn = ttk.Button(master=self._action_lf)
        self._open_input_img_btn = ttk.Button(master=self._action_lf)
        self._delete_input_img_btn = ttk.Button(master=self._action_lf)
        self._add_btn = ttk.Button(master=self._action_lf)
        self._delete_btn = ttk.Button(master=self._action_lf)
        self._training_btn = ttk.Button(master=self._action_lf)
        self._process_pb = ttk.Progressbar(master=self._action_lf)

        self._opened_files_lf = ttk.Labelframe(master=self._action_lf)
        self._opened_files_lb = tk.Listbox(master=self._opened_files_lf)
        self._opened_files_sb_x = AutoScrollbar(master=self._opened_files_lf, orient="horizontal")
        self._opened_files_sb_y = AutoScrollbar(master=self._opened_files_lf, orient="vertical")

        self._input_frame = ttk.Labelframe(master=self._action_lf)
        self._mc_id_label = ttk.Label(master=self._input_frame)
        self._mc_name_label = ttk.Label(master=self._input_frame)
        self._mc_spinbox = ttk.Spinbox(master=self._input_frame)
        self._mc_input = ttk.Entry(master=self._input_frame)
        self._color_label = ttk.Label(master=self._input_frame)
        self._color_btn = tk.Button(master=self._input_frame)

        self._treeview_frame = ttk.Frame(master=self._action_lf)
        self._treeview = ttk.Treeview(master=self._treeview_frame)
        self._treeview_sb_y = ttk.Scrollbar(master=self._treeview_frame, orient="vertical")

        # initialize canvas components
        self._canvas_lf = ttk.Labelframe(master=self)

        # initialize ttk.Variables
        self._setup_vars()

    def _configure_components(self) -> None:
        """
        Configures the visual components.

        :return: None
        """

        # configure user action components
        self._action_lf.configure(text="Actions", padding=10)
        self._back_btn.configure(text="Back to main window")
        self._open_input_img_btn.configure(text="Open training image")
        self._delete_input_img_btn.configure(text="Delete training image")

        self._opened_files_lf.configure(text="Opened files", padding=10)
        self._opened_files_lb.configure(
            selectmode=SINGLE,
            exportselection=False,
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#919191",
            selectforeground="#ffffff",
            background="#ffffff",
            foreground="#555555",
            yscrollcommand=self._opened_files_sb_y.set,
            xscrollcommand=self._opened_files_sb_x.set
        )
        self._opened_files_sb_x.configure(orient=HORIZONTAL, command=self._opened_files_lb.xview)
        self._opened_files_sb_y.configure(orient=VERTICAL, command=self._opened_files_lb.yview)

        self._opened_files_lf.rowconfigure(0, weight=1)
        self._opened_files_lf.columnconfigure(0, weight=1)

        self._add_btn.configure(text="Add new Class")
        self._delete_btn.configure(text="Delete Class")
        self._training_btn.configure(text="Start training")
        self._process_pb.configure(value=0, mode="determinate")

        self._input_frame.configure(text="Class settings", padding=(20, 10, 10, 15))
        self._mc_id_label.configure(text="Class ID:")
        self._mc_name_label.configure(text="Class Name:")
        self._mc_spinbox.configure(width=4, textvariable=self._vars["mc_id_spinbox"], from_=1, increment=1, to=15)
        self._mc_input.configure(width=15)
        self._mc_input.insert(0, "Garbage")
        self._color_label.configure(text="Color:")
        self._color_btn.configure(width=10, bg="#ff4136", activebackground="#ff4136")

        self._treeview.configure(columns=("0", "1", "2"), show="headings", height=5,
                                 selectmode="browse", yscrollcommand=self._treeview_sb_y.set)
        self._treeview.heading("0", text="NAME")
        self._treeview.heading("1", text="CLASS ID")
        self._treeview.heading("2", text="TAG ID")

        self._treeview.column("0", width=144, stretch=NO, anchor=CENTER)
        self._treeview.column("1", width=80, stretch=NO, anchor=CENTER)
        self._treeview.column("2", width=119, stretch=NO, anchor=CENTER)

        self._treeview_sb_y.configure(orient=VERTICAL, command=self._treeview.yview)

        for i in range(12):
            if 6 <= i <= 9:
                self._action_lf.rowconfigure(i, weight=5)
            else:
                self._action_lf.rowconfigure(i, weight=1)

        self._action_lf.columnconfigure(0, weight=1)
        self._action_lf.columnconfigure(1, weight=1)

        for i in range(3):
            self._input_frame.columnconfigure(i, weight=1)

        self._input_frame.rowconfigure(0, weight=1)
        self._input_frame.rowconfigure(1, weight=1)

        self._treeview_frame.rowconfigure(0, weight=1)
        self._treeview_frame.columnconfigure(0, weight=1)

        # configure canvas components
        self._canvas_lf.configure(text="Image", padding=10)

    def _style_components(self) -> None:
        """
        Sets style of visual components.

        :return: None
        """

        # style user action components
        self._action_lf["bootstyle"] = "default"
        self._back_btn["bootstyle"] = "dark"
        self._open_input_img_btn["bootstyle"] = "primary"
        self._delete_input_img_btn["bootstyle"] = "danger"
        self._add_btn["bootstyle"] = "success"
        self._delete_btn["bootstyle"] = "danger"
        self._training_btn["bootstyle"] = "warning"
        self._process_pb["bootstyle"] = "warning"

        self._opened_files_lf["bootstyle"] = "default"
        self._opened_files_sb_x["bootstyle"] = "default"
        self._opened_files_sb_y["bootstyle"] = "default"

        self._input_frame["bootstyle"] = "default"
        self._mc_id_label["bootstyle"] = "default"
        self._mc_name_label["bootstyle"] = "default"
        self._mc_spinbox["bootstyle"] = "default"
        self._mc_input["bootstyle"] = "default"
        self._color_label["bootstyle"] = "default"

        self._treeview["bootstyle"] = "dark"
        self._treeview_sb_y["bootstyle"] = "default"

        # style canvas components
        self._canvas_lf["bootstyle"] = "default"

    def _place_components(self) -> None:
        """
        Places the visual components on the window.

        :return: None
        """

        # place user action components
        self._action_lf.place(x=20, y=10, height=870, width=400)
        self._back_btn.grid(row=0, column=0, columnspan=2, sticky="ns", padx=5, pady=5)
        self._open_input_img_btn.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self._delete_input_img_btn.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self._opened_files_lf.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self._opened_files_lb.grid(row=0, column=0, sticky="nsew")
        self._opened_files_sb_x.grid(row=1, column=0, sticky="ew")
        self._opened_files_sb_y.grid(row=0, column=1, sticky="ns")

        self._add_btn.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        self._delete_btn.grid(row=4, column=1, sticky="nsew", padx=5, pady=5)
        self._input_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self._treeview_frame.grid(row=6, column=0, rowspan=4, columnspan=2, sticky="nsew", padx=5, pady=5)
        self._training_btn.grid(row=10, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self._process_pb.grid(row=11, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self._mc_id_label.grid(row=0, column=0, sticky="sw", padx=5, pady=5)
        self._mc_name_label.grid(row=0, column=1, sticky="sw", padx=5, pady=5)
        self._color_label.grid(row=0, column=2, sticky="sw", padx=5, pady=5)
        self._mc_spinbox.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self._mc_input.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self._color_btn.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        self._treeview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self._treeview_sb_y.grid(row=0, column=1, sticky="ns")

        # place canvas components
        self._canvas_lf.place(x=440, y=10, height=870, width=1140)

    def _setup_vars(self) -> None:
        """
        Sets up the ttk.Variables.

        :return: None
        """

        self._vars = dict()
        self._vars["mc_id_spinbox"] = ttk.IntVar(master=self, value=1)
