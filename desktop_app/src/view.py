import tkinter as tk
import tkinter.messagebox
import ttkbootstrap as ttk

from matplotlib import cm
from model.exceptions import *
from PIL import ImageTk, Image
from ttkbootstrap.constants import *
from typing import List, Dict, Tuple, Union
from matplotlib.colors import ListedColormap
from desktop_app.src.settings_view import SettingsView
from desktop_app.src.auto_scrollbar import AutoScrollbar
from desktop_app.src.training_view import TrainingView, ZoomCanvas


THEME = "lumen"
SIZE = "1600x880"


class View(ttk.Window):
    """
    The View layer of the application.

    """

    def __init__(self) -> None:
        """
        The constructor of the View class.

        """

        super(View, self).__init__(themename=THEME)

        self._initialize_components()
        self._configure_components()
        self._style_components()
        self._place_components()

        self._training_view = TrainingView(self)
        self._settings_view = SettingsView(self)

    # Class properties
    @property
    def vars(self) -> Dict[str, ttk.Variable]:
        return self._vars

    @property
    def menubar(self) -> ttk.Menu:
        return self._menubar

    @property
    def process_menu(self) -> ttk.Menu:
        return self._process_menu

    @property
    def process_btn(self) -> ttk.Menubutton:
        return self._process_btn

    @property
    def add_files_btn(self) -> ttk.Button:
        return self._add_files_btn

    @property
    def delete_files_btn(self) -> ttk.Button:
        return self._delete_files_btn

    @property
    def opened_files_lb(self) -> tk.Listbox:
        return self._opened_files_lb

    @property
    def start_process_btn(self) -> ttk.Button:
        return self._start_process_btn

    @property
    def train_rf_btn(self) -> ttk.Button:
        return self._train_rf_btn

    @property
    def process_pb(self) -> ttk.Progressbar:
        return self._process_pb

    @property
    def coord_btn(self) -> ttk.Button:
        return self._coord_btn

    @property
    def estimate_area_btn(self) -> ttk.Button:
        return self._estimate_area_btn

    @property
    def training_view(self) -> TrainingView:
        return self._training_view

    @property
    def settings_view(self) -> SettingsView:
        return self._settings_view

    @property
    def left_canvas(self) -> ZoomCanvas:
        return self._left_canvas

    @property
    def right_canvas(self) -> ZoomCanvas:
        return self._right_canvas

    @property
    def left_img_lf(self) -> ttk.Labelframe:
        return self._left_img_lf

    @property
    def right_img_lf(self) -> ttk.Labelframe:
        return self._right_img_lf

    # Non-static public methods
    # def report_callback_exception(self, exc, val, tb) -> None:
    #     """
    #     Alerts the user if some exception occurred with a Messagebox.
    #
    #     """
    #
    #     parent = self.get_active_window()
    #
    #     tkinter.messagebox.showerror(
    #         parent=parent,
    #         title="Error",
    #         message=str(val)
    #     )

    def get_active_window(self) -> Union[ttk.Window, ttk.Toplevel]:
        """
        Returns the active window.

        :return: active window
        """

        parent = None

        if self._training_view.state() == "normal":
            parent = self._training_view
        elif self._settings_view.state() == "normal":
            parent = self._settings_view
        else:
            parent = self

        return parent

    def show(self) -> None:
        """
        Displays the main window.

        :return:
        """

        self.title("Waste monitoring")
        self.resizable(width=False, height=False)
        self.geometry(SIZE)
        self.attributes("-topmost", True)
        self.update()
        self.attributes("-topmost", False)
        self.place_window_center()
        self.mainloop()

    def add_file_to_listbox(self, file: str) -> None:
        """
        Adds file to listbox.

        :param file: file name to be added
        :return: None
        """

        self._opened_files_lb.insert(END, file)

    def remove_file_from_listbox(self, file_index: int) -> None:
        """
        Removes file from listbox.

        :param file_index: index of the file to be removed
        :return: None
        """

        self._opened_files_lb.delete(file_index)

    def get_curselection_indices_listbox(self) -> Tuple[int, ...]:
        """
        Returns the indices of the currently selected items in the listbox.

        :return: tuple of indices
        """

        return self._opened_files_lb.curselection()

    def get_curselection_values_listbox(self) -> List[str]:
        """
        Returns the values of the currently selected items in the listbox.

        :return: list of string values
        """

        selected_indices = self.get_curselection_indices_listbox()
        selected_values = [self._opened_files_lb.get(index) for index in selected_indices]
        return selected_values

    def show_image_on_canvas(
        self,
        canvas_name: str,
        img_or_array: str,
        image_type: str,
        satellite_rgb: List[int],
        color_map: ListedColormap = cm.get_cmap("viridis"),
    ) -> None:
        """
        Displays image on the specified canvas with the given color map.

        :param canvas_name: "left" or "right"
        :param img_or_array: path of the image to be displayed
        :param image_type: "rgb", "classified" or "heatmap"
        :param satellite_rgb: indices of RGB bands on satellite image
        :param color_map: color map
        :return: None
        :raise CanvasNameException: if given parameter canvas_name is wrong
        """

        if canvas_name.lower() not in ["left", "right"]:
            raise CanvasNameException(canvas_name.lower())

        canvas = self._left_canvas if canvas_name.lower() == "left" else self._right_canvas

        canvas.open_image(img_or_array, image_type.lower(), satellite_rgb, color_map)

    def clear_canvas(self, canvas_name: str) -> None:
        """
        Clears the specified canvas.

        :param canvas_name: "left" or "right"
        :return: None
        """

        if canvas_name.lower() == "left":
            self._left_canvas.delete_image()
            self._left_img_lf.configure(text="")
        elif canvas_name.lower() == "right":
            self._right_canvas.delete_image()
            self._right_img_lf.configure(text="")

    def change_start_process_btn_state(self, active: bool) -> None:
        """
        Activates or disables the Start Processing button.

        :param active: True or False
        :return: None
        """

        state = NORMAL if active else DISABLED
        self._start_process_btn.configure(state=state)
        self._start_process_btn.update()

    # Non-static protected methods
    def _initialize_components(self) -> None:
        """
        Initializes the visual components.

        :return: None
        """

        # initialize menu controls
        self._menubar = ttk.Menu(master=self)
        self._file_menu = ttk.Menu(master=self._menubar)
        self._settings_menu = ttk.Menu(master=self._menubar)
        self._help_menu = ttk.Menu(master=self._menubar)

        # initialize action controls
        self._action_lf = ttk.Labelframe(master=self)
        self._process_menu = ttk.Menu(master=self._action_lf)
        self._process_btn = ttk.Menubutton(master=self._action_lf, menu=self._process_menu)
        self._add_files_btn = ttk.Button(master=self._action_lf)
        self._delete_files_btn = ttk.Button(master=self._action_lf)

        # initialize opened files controls
        self._opened_files_lf = ttk.Labelframe(master=self)
        self._opened_files_lb = tk.Listbox(master=self._opened_files_lf)
        self._opened_files_sb_x = AutoScrollbar(master=self._opened_files_lf, orient="horizontal")
        self._opened_files_sb_y = AutoScrollbar(master=self._opened_files_lf, orient="vertical")

        # initialize processing controls
        self._start_process_lf = ttk.Labelframe(master=self)
        self._train_rf_btn = ttk.Button(master=self._start_process_lf)
        self._start_process_btn = ttk.Button(master=self._start_process_lf)
        self._process_pb = ttk.Progressbar(master=self._start_process_lf)

        # initialize statistics controls
        self._stats_lf = ttk.Labelframe(master=self)
        self._coord_btn = ttk.Button(master=self._stats_lf)
        self._estimate_area_btn = ttk.Button(master=self._stats_lf)

        self._heatmap_frame = ttk.Frame(master=self._stats_lf)
        self._heatmap_checkbutton = ttk.Checkbutton(master=self._heatmap_frame)
        self._high_checkbutton = ttk.Checkbutton(master=self._heatmap_frame)
        self._medium_checkbutton = ttk.Checkbutton(master=self._heatmap_frame)
        self._low_checkbutton = ttk.Checkbutton(master=self._heatmap_frame)
        self._img_label = ttk.Label(master=self._stats_lf)

        # initialize left canvas controls
        self._left_img_lf = ttk.Labelframe(master=self)
        self._left_canvas = ZoomCanvas(self._left_img_lf)

        # initialize right canvas controls
        self._right_img_lf = ttk.Labelframe(master=self)
        self._right_canvas = ZoomCanvas(self._right_img_lf)

        # initialize vars
        self._setup_vars()

    def _configure_components(self) -> None:
        """
        Configures the visual components.

        :return: None
        """

        # configure menu controls
        self._menubar.configure(None)
        self._file_menu.configure(tearoff=False)
        self._settings_menu.configure(tearoff=False)
        self._help_menu.configure(tearoff=False)

        self._setup_menu()

        # configure action controls
        self._action_lf.configure(text="Actions", padding=10)
        self._process_menu.configure(None)
        self._process_btn.configure(text="Select process")
        self._add_files_btn.configure(text="Add files")
        self._delete_files_btn.configure(text="Delete files")

        self._setup_process_menu()

        # configure opened files controls
        self._opened_files_lf.configure(text="Opened files", padding=10)
        self._opened_files_lb.configure(
            selectmode=EXTENDED,
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#919191",
            selectforeground="#ffffff",
            background="#ffffff",
            foreground="#555555",
            yscrollcommand=self._opened_files_sb_y.set,
            xscrollcommand=self._opened_files_sb_x.set,
        )
        self._opened_files_sb_x.configure(orient=HORIZONTAL, command=self._opened_files_lb.xview)
        self._opened_files_sb_y.configure(orient=VERTICAL, command=self._opened_files_lb.yview)

        self._opened_files_lf.rowconfigure(0, weight=1)
        self._opened_files_lf.columnconfigure(0, weight=1)

        # configure processing controls
        self._start_process_lf.configure(text="Processing", padding=(10, 20, 10, 20))
        self._train_rf_btn.configure(text="Train Random Forest")
        self._start_process_btn.configure(text="Start processing", state=DISABLED)
        self._process_pb.configure(value=0, mode="determinate")

        # configure statistics controls
        self._stats_lf.configure(text="Statistics", padding=(20, 30, 10, 30))
        self._coord_btn.configure(text="Save polluted areas to GeoJSON file")
        self._estimate_area_btn.configure(text="Estimate polluted areas")

        self._heatmap_frame.configure(None)
        self._heatmap_checkbutton.configure(text="Show Heatmap", variable=self._vars["heatmap_toggle"])
        self._high_checkbutton.configure(text="High probability", variable=self._vars["heatmap_high"])
        self._medium_checkbutton.configure(text="Medium probability", variable=self._vars["heatmap_medium"])
        self._low_checkbutton.configure(text="Low probability", variable=self._vars["heatmap_low"])

        self._image = ImageTk.PhotoImage(Image.open("desktop_app/resources/icon.png").resize((128, 128)))
        self._img_label.configure(image=self._image)

        self._stats_lf.columnconfigure(0, weight=5)
        self._stats_lf.columnconfigure(1, weight=1)
        self._stats_lf.columnconfigure(2, weight=5)

        for i in range(2):
            self._stats_lf.rowconfigure(i, weight=1)

        # configure left canvas controls
        self._left_img_lf.configure(text="", padding=10)

        # configure right canvas controls
        self._right_img_lf.configure(text="", padding=10)

    def _style_components(self) -> None:
        """
        Sets style of visual components.

        :return: None
        """

        # style action controls
        self._action_lf["bootstyle"] = "default"
        self._process_btn["bootstyle"] = "primary"
        self._add_files_btn["bootstyle"] = "success"
        self._delete_files_btn["bootstyle"] = "danger"

        # style opened files controls
        self._opened_files_lf["bootstyle"] = "default"
        self._opened_files_sb_x["bootstyle"] = "default"
        self._opened_files_sb_y["bootstyle"] = "default"

        # style processing controls
        self._start_process_lf["bootstyle"] = "default"
        self._train_rf_btn["bootstyle"] = "success"
        self._start_process_btn["bootstyle"] = "warning"
        self._process_pb["bootstyle"] = "warning"

        # style statistics controls
        self._stats_lf["bootstyle"] = "default"
        self._coord_btn["bootstyle"] = "primary"
        self._estimate_area_btn["bootstyle"] = "warning"

        self._heatmap_frame["bootstyle"] = "default"
        self._heatmap_checkbutton["bootstyle"] = "danger-round-toggle"
        self._high_checkbutton["bootstyle"] = "danger"
        self._medium_checkbutton["bootstyle"] = "warning"
        self._low_checkbutton["bootstyle"] = "success"
        self._img_label["bootstyle"] = "default"

        # style left canvas controls
        self._left_img_lf["bootstyle"] = "default"

        # initialize right canvas controls
        self._right_img_lf["bootstyle"] = "default"

    def _place_components(self) -> None:
        """
        Places the visual components on the window.

        :return: None
        """

        # place action controls
        self._action_lf.place(x=20, y=10, height=200, width=225)
        self._process_btn.pack(side=TOP, expand=YES, padx=5, pady=5, fill=BOTH)
        self._add_files_btn.pack(side=TOP, expand=YES, padx=5, pady=5, fill=BOTH)
        self._delete_files_btn.pack(side=TOP, expand=YES, padx=5, pady=5, fill=BOTH)

        # place opened files controls
        self._opened_files_lf.place(x=265, y=10, height=200, width=390)
        self._opened_files_lb.grid(row=0, column=0, sticky="nsew")
        self._opened_files_sb_x.grid(row=1, column=0, sticky="ew")
        self._opened_files_sb_y.grid(row=0, column=1, sticky="ns")

        # place processing controls
        self._start_process_lf.place(x=675, y=10, height=200, width=250)
        self._train_rf_btn.pack(side=TOP, expand=YES, padx=5, pady=5, fill=BOTH)
        self._start_process_btn.pack(side=TOP, expand=YES, padx=5, pady=5, fill=BOTH)
        self._process_pb.pack(side=TOP, expand=NO, padx=5, pady=5, fill=X)

        # place statistics controls
        self._stats_lf.place(x=945, y=10, height=200, width=635)
        # self._show_heatmap_btn.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self._coord_btn.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self._estimate_area_btn.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self._img_label.grid(row=0, column=2, rowspan=2, sticky="e", padx=5, pady=5)

        self._heatmap_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        self._heatmap_checkbutton.pack(side=TOP, expand=YES, padx=5, pady=5, fill=BOTH)
        self._high_checkbutton.pack(side=TOP, expand=YES, padx=40, pady=5, fill=X)
        self._medium_checkbutton.pack(side=TOP, expand=YES, padx=40, pady=5, fill=X)
        self._low_checkbutton.pack(side=TOP, expand=YES, padx=40, pady=5, fill=X)

        # place left canvas controls
        self._left_img_lf.place(x=20, y=220, height=640, width=770)

        # place right canvas controls
        self._right_img_lf.place(x=810, y=220, height=640, width=770)

    def _setup_vars(self) -> None:
        """
        Initializes the ttk.Variables of this class.

        :return: None
        """

        self._vars = dict()
        self._vars["process_menu"] = ttk.IntVar(master=self)
        self._vars["heatmap_toggle"] = ttk.IntVar(master=self)
        self._vars["heatmap_high"] = ttk.IntVar(master=self)
        self._vars["heatmap_medium"] = ttk.IntVar(master=self)
        self._vars["heatmap_low"] = ttk.IntVar(master=self)

    def _setup_menu(self) -> None:
        """
        Sets the menubar of the application.

        :return: None
        """

        self.configure(menu=self._menubar)

    def _setup_process_menu(self) -> None:
        """
        Sets up the process menu.

        :return: None
        """

        self._process_menu.add_radiobutton(label="Hot-spot detection", value=1, variable=self._vars["process_menu"])
        self._process_menu.add_radiobutton(
            label="Floating waste detection",
            value=2,
            variable=self._vars["process_menu"],
        )
        self._process_menu.add_radiobutton(
            label="Washed up waste detection",
            value=3,
            variable=self._vars["process_menu"],
        )
        self._process_menu.add_radiobutton(label="Process with UNET", value=4, variable=self._vars["process_menu"])
