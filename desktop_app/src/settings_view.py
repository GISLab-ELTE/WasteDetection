import tkinter as tk
import ttkbootstrap as ttk

from typing import List, Dict
from ttkbootstrap.tooltip import ToolTip


THEME = "lumen"
SIZE = "1090x730"


class SettingsView(ttk.Toplevel):
    """
    Settings window for the View class.

    """

    def __init__(self, master: ttk.Window):
        """
        Constructor of the SettingsView class.

        :param master: parent window
        """

        super(SettingsView, self).__init__(master=master)

        self._configure_window()
        self._initialize_components()
        self._configure_components()
        self._style_components()
        self._place_components()

        self.withdraw()

    # Class properties
    @property
    def vars(self) -> Dict[str, ttk.Variable]:
        return self._vars

    @property
    def planet_rb(self) -> ttk.Radiobutton:
        return self._planet_rb

    @property
    def sentinel_rb(self) -> ttk.Radiobutton:
        return self._sentinel_rb

    @property
    def sentinel_blue_spinbox(self) -> ttk.Spinbox:
        return self._sentinel_blue_spinbox

    @property
    def sentinel_green_spinbox(self) -> ttk.Spinbox:
        return self._sentinel_green_spinbox

    @property
    def sentinel_red_spinbox(self) -> ttk.Spinbox:
        return self._sentinel_red_spinbox

    @property
    def sentinel_nir_spinbox(self) -> ttk.Spinbox:
        return self._sentinel_nir_spinbox

    @property
    def training_estimators_entry(self) -> ttk.Entry:
        return self._training_estimators_entry

    @property
    def morphology_matrix_spinbox(self) -> ttk.Spinbox:
        return self._morphology_matrix_spinbox

    @property
    def morphology_iterations_spinbox(self) -> ttk.Spinbox:
        return self._morphology_iterations_spinbox

    @property
    def washed_up_heatmap_sections_spinbox(self) -> ttk.Spinbox:
        return self._washed_up_heatmap_sections_spinbox

    @property
    def heatmap_high_spinbox(self) -> ttk.Spinbox:
        return self._heatmap_high_spinbox

    @property
    def heatmap_medium_spinbox(self) -> ttk.Spinbox:
        return self._heatmap_medium_spinbox

    @property
    def heatmap_low_spinbox(self) -> ttk.Spinbox:
        return self._heatmap_low_spinbox

    @property
    def garbage_c_id_spinbox(self) -> ttk.Spinbox:
        return self._garbage_c_id_spinbox

    @property
    def water_c_id_spinbox(self) -> ttk.Spinbox:
        return self._water_c_id_spinbox

    @property
    def working_dir_entry(self) -> ttk.Entry:
        return self._working_dir_entry

    @property
    def working_dir_browse_btn(self) -> ttk.Button:
        return self._working_dir_browse_btn

    @property
    def hotspot_rf_entry(self) -> ttk.Entry:
        return self._hotspot_rf_entry

    @property
    def hotspot_rf_browse_btn(self) -> ttk.Button:
        return self._hotspot_rf_browse_btn

    @property
    def floating_rf_entry(self) -> ttk.Entry:
        return self._floating_rf_entry

    @property
    def floating_rf_browse_btn(self) -> ttk.Button:
        return self._floating_rf_browse_btn

    @property
    def file_extension_entry(self) -> ttk.Entry:
        return self._file_extension_entry

    @property
    def hotspot_classified_postfix_entry(self) -> ttk.Entry:
        return self._hotspot_classified_postfix_entry

    @property
    def hotspot_heatmap_postfix_entry(self) -> ttk.Entry:
        return self._hotspot_heatmap_postfix_entry

    @property
    def floating_classified_postfix_entry(self) -> ttk.Entry:
        return self._floating_classified_postfix_entry

    @property
    def floating_heatmap_postfix_entry(self) -> ttk.Entry:
        return self._floating_heatmap_postfix_entry

    @property
    def floating_masked_classified_postfix_entry(self) -> ttk.Entry:
        return self._floating_masked_classified_postfix_entry

    @property
    def floating_masked_heatmap_postfix_entry(self) -> ttk.Entry:
        return self._floating_masked_heatmap_postfix_entry

    @property
    def washed_up_before_postfix_entry(self) -> ttk.Entry:
        return self._washed_up_before_postfix_entry

    @property
    def washed_up_after_postfix_entry(self) -> ttk.Entry:
        return self._washed_up_after_postfix_entry

    @property
    def color_buttons(self) -> List[tk.Button]:
        return self._color_buttons

    @property
    def ok_btn(self) -> ttk.Button:
        return self._ok_btn

    @property
    def cancel_btn(self) -> ttk.Button:
        return self._cancel_btn

    # Non-static public methods
    def show(self) -> None:
        """
        Displays window if it is hidden.

        :return: None
        """

        self.grab_set()
        self.update()
        self.deiconify()

    def hide(self) -> None:
        """
        Hides window if it is visible.

        :return: None
        """

        self.withdraw()
        self.grab_release()

    # Non-static protected methods
    def _configure_window(self) -> None:
        """
        Configures the window.

        :return: None
        """

        self.title("Settings")
        self.resizable(width=False, height=False)
        self.geometry(SIZE)
        self.place_window_center()

    def _initialize_components(self) -> None:
        """
        Initializes the visual components.

        :return: None
        """

        self._color_buttons = list()
        self._color_labels = list()

        self._satellite_lf = ttk.Labelframe(master=self)

        self._planet_rb = ttk.Radiobutton(master=self._satellite_lf)
        self._sentinel_rb = ttk.Radiobutton(master=self._satellite_lf)

        self._sentinel_settings_lf = ttk.Labelframe(master=self)

        self._sentinel_blue_label = ttk.Label(master=self._sentinel_settings_lf)
        self._sentinel_blue_spinbox = ttk.Spinbox(master=self._sentinel_settings_lf)

        self._sentinel_green_label = ttk.Label(master=self._sentinel_settings_lf)
        self._sentinel_green_spinbox = ttk.Spinbox(master=self._sentinel_settings_lf)

        self._sentinel_red_label = ttk.Label(master=self._sentinel_settings_lf)
        self._sentinel_red_spinbox = ttk.Spinbox(master=self._sentinel_settings_lf)

        self._sentinel_nir_label = ttk.Label(master=self._sentinel_settings_lf)
        self._sentinel_nir_spinbox = ttk.Spinbox(master=self._sentinel_settings_lf)

        self._value_settings_lf = ttk.Labelframe(master=self)

        self._training_estimators_label = ttk.Label(master=self._value_settings_lf)
        self._training_estimators_entry = ttk.Entry(master=self._value_settings_lf)

        self._morphology_matrix_label = ttk.Label(master=self._value_settings_lf)
        self._morphology_matrix_spinbox = ttk.Spinbox(master=self._value_settings_lf)

        self._morphology_iterations_label = ttk.Label(master=self._value_settings_lf)
        self._morphology_iterations_spinbox = ttk.Spinbox(
            master=self._value_settings_lf
        )

        self._washed_up_heatmap_sections_label = ttk.Label(
            master=self._value_settings_lf
        )
        self._washed_up_heatmap_sections_spinbox = ttk.Spinbox(
            master=self._value_settings_lf
        )

        self._heatmap_high_label = ttk.Label(master=self._value_settings_lf)
        self._heatmap_high_spinbox = ttk.Spinbox(master=self._value_settings_lf)

        self._heatmap_medium_label = ttk.Label(master=self._value_settings_lf)
        self._heatmap_medium_spinbox = ttk.Spinbox(master=self._value_settings_lf)

        self._heatmap_low_label = ttk.Label(master=self._value_settings_lf)
        self._heatmap_low_spinbox = ttk.Spinbox(master=self._value_settings_lf)

        self._c_id_frame = ttk.Frame(master=self._value_settings_lf)

        self._garbage_c_id_label = ttk.Label(master=self._c_id_frame)
        self._garbage_c_id_spinbox = ttk.Spinbox(master=self._c_id_frame)

        self._water_c_id_label = ttk.Label(master=self._c_id_frame)
        self._water_c_id_spinbox = ttk.Spinbox(master=self._c_id_frame)

        self._paths_lf = ttk.Labelframe(master=self)

        self._working_dir_label = ttk.Label(master=self._paths_lf)
        self._working_dir_entry = ttk.Entry(master=self._paths_lf)
        self._working_dir_browse_btn = ttk.Button(master=self._paths_lf)

        self._hotspot_rf_label = ttk.Label(master=self._paths_lf)
        self._hotspot_rf_entry = ttk.Entry(master=self._paths_lf)
        self._hotspot_rf_browse_btn = ttk.Button(master=self._paths_lf)

        self._floating_rf_label = ttk.Label(master=self._paths_lf)
        self._floating_rf_entry = ttk.Entry(master=self._paths_lf)
        self._floating_rf_browse_btn = ttk.Button(master=self._paths_lf)

        self._file_settings_lf = ttk.Labelframe(master=self)

        self._file_extension_label = ttk.Label(master=self._file_settings_lf)
        self._file_extension_entry = ttk.Entry(master=self._file_settings_lf)

        self._hotspot_classified_postfix_label = ttk.Label(
            master=self._file_settings_lf
        )
        self._hotspot_classified_postfix_entry = ttk.Entry(
            master=self._file_settings_lf
        )

        self._hotspot_heatmap_postfix_label = ttk.Label(master=self._file_settings_lf)
        self._hotspot_heatmap_postfix_entry = ttk.Entry(master=self._file_settings_lf)

        self._floating_classified_postfix_label = ttk.Label(
            master=self._file_settings_lf
        )
        self._floating_classified_postfix_entry = ttk.Entry(
            master=self._file_settings_lf
        )

        self._floating_heatmap_postfix_label = ttk.Label(master=self._file_settings_lf)
        self._floating_heatmap_postfix_entry = ttk.Entry(master=self._file_settings_lf)

        self._floating_masked_classified_postfix_label = ttk.Label(
            master=self._file_settings_lf
        )
        self._floating_masked_classified_postfix_entry = ttk.Entry(
            master=self._file_settings_lf
        )

        self._floating_masked_heatmap_postfix_label = ttk.Label(
            master=self._file_settings_lf
        )
        self._floating_masked_heatmap_postfix_entry = ttk.Entry(
            master=self._file_settings_lf
        )

        self._washed_up_before_postfix_label = ttk.Label(master=self._file_settings_lf)
        self._washed_up_before_postfix_entry = ttk.Entry(master=self._file_settings_lf)

        self._washed_up_after_postfix_label = ttk.Label(master=self._file_settings_lf)
        self._washed_up_after_postfix_entry = ttk.Entry(master=self._file_settings_lf)

        self._training_labels = ttk.Labelframe(master=self)

        self._training_blue = ttk.Checkbutton(master=self._training_labels)
        self._training_green = ttk.Checkbutton(master=self._training_labels)
        self._training_red = ttk.Checkbutton(master=self._training_labels)
        self._training_nir = ttk.Checkbutton(master=self._training_labels)
        self._training_pi = ttk.Checkbutton(master=self._training_labels)
        self._training_ndwi = ttk.Checkbutton(master=self._training_labels)
        self._training_ndvi = ttk.Checkbutton(master=self._training_labels)
        self._training_rndvi = ttk.Checkbutton(master=self._training_labels)
        self._training_sr = ttk.Checkbutton(master=self._training_labels)
        self._training_apwi = ttk.Checkbutton(master=self._training_labels)

        self._color_settings = ttk.Labelframe(master=self)

        for i in range(16):
            self._color_labels.append(ttk.Label(master=self._color_settings))
            self._color_buttons.append(tk.Button(master=self._color_settings))

        self._ok_btn = ttk.Button(master=self)
        self._cancel_btn = ttk.Button(master=self)

        self._setup_vars()

    def _configure_components(self) -> None:
        """
        Configures the visual components.

        :return: None
        """

        self._satellite_lf.configure(text="Satellite type", padding=10)
        self._satellite_lf.rowconfigure(0, weight=1)
        self._satellite_lf.columnconfigure(0, weight=1)
        self._satellite_lf.columnconfigure(1, weight=1)

        self._planet_rb.configure(
            text="Planet", variable=self._vars["satellite_rb"], value=1
        )
        self._sentinel_rb.configure(
            text="Sentinel-2", variable=self._vars["satellite_rb"], value=2
        )

        self._sentinel_settings_lf.configure(text="Sentinel-2 settings", padding=10)
        for i in range(8):
            self._sentinel_settings_lf.columnconfigure(i, weight=1)
        self._sentinel_settings_lf.rowconfigure(0, weight=1)

        self._sentinel_blue_label.configure(text="Blue band:")
        self._sentinel_blue_spinbox.configure(width=2, from_=1, increment=1, to=13)

        self._sentinel_green_label.configure(text="Green band:")
        self._sentinel_green_spinbox.configure(width=2, from_=1, increment=1, to=13)

        self._sentinel_red_label.configure(text="Red band:")
        self._sentinel_red_spinbox.configure(width=2, from_=1, increment=1, to=13)

        self._sentinel_nir_label.configure(text="NIR band:")
        self._sentinel_nir_spinbox.configure(width=2, from_=1, increment=1, to=13)

        self._value_settings_lf.configure(text="Algorithm settings", padding=10)
        for i in range(4):
            self._value_settings_lf.rowconfigure(i, weight=1)
            self._value_settings_lf.columnconfigure(i, weight=1)

        self._training_estimators_label.configure(
            text="Number of decision trees in Random Forest:"
        )
        self._training_estimators_entry.configure(width=2)

        self._morphology_matrix_label.configure(
            text="Matrix size for morphology (NxN):"
        )
        self._morphology_matrix_spinbox.configure(width=2, from_=1, increment=1, to=20)

        self._morphology_iterations_label.configure(
            text="Number of iterations for morphology:"
        )
        self._morphology_iterations_spinbox.configure(
            width=2, from_=1, increment=1, to=20
        )

        self._washed_up_heatmap_sections_label.configure(
            text="Washed up waste pixel uniqueness modifier:"
        )
        self._washed_up_heatmap_sections_spinbox.configure(
            width=2, from_=4, increment=1, to=20
        )

        self._heatmap_high_label.configure(text="Heatmap high probability (%):")
        self._heatmap_high_spinbox.configure(width=2, from_=1, increment=1, to=100)

        self._heatmap_medium_label.configure(text="Heatmap medium probability (%):")
        self._heatmap_medium_spinbox.configure(width=2, from_=1, increment=1, to=100)

        self._heatmap_low_label.configure(text="Heatmap low probability (%):")
        self._heatmap_low_spinbox.configure(width=2, from_=1, increment=1, to=100)

        self._c_id_frame.configure(None)
        for i in range(4):
            self._c_id_frame.columnconfigure(i, weight=1)
        self._c_id_frame.rowconfigure(0, weight=1)

        self._garbage_c_id_label.configure(text="Garbage Class ID:")
        self._garbage_c_id_spinbox.configure(width=2, from_=1, increment=1, to=15)

        self._water_c_id_label.configure(text="Water Class ID:")
        self._water_c_id_spinbox.configure(width=2, from_=1, increment=1, to=15)

        self._paths_lf.configure(text="Path settings", padding=10)
        for i in range(4):
            self._paths_lf.rowconfigure(i, weight=1)
        self._paths_lf.columnconfigure(0, weight=4)
        self._paths_lf.columnconfigure(1, weight=10)
        self._paths_lf.columnconfigure(2, weight=1)

        self._working_dir_label.configure(text="Working Directory:")
        self._working_dir_entry.configure(validate="all", width=40)
        self._working_dir_browse_btn.configure(text="...")

        self._hotspot_rf_label.configure(text="Random Forest for Hot-spot detection:")
        self._hotspot_rf_entry.configure(validate="all", width=40)
        self._hotspot_rf_browse_btn.configure(text="...")

        self._floating_rf_label.configure(
            text="Random Forest for Floating waste detection:"
        )
        self._floating_rf_entry.configure(validate="all", width=40)
        self._floating_rf_browse_btn.configure(text="...")

        self._file_settings_lf.configure(text="Output file settings", padding=10)
        for i in range(5):
            self._file_settings_lf.rowconfigure(i, weight=1)
        for i in range(4):
            self._file_settings_lf.columnconfigure(i, weight=1)

        self._file_extension_label.configure(text="File extension:")
        self._file_extension_entry.configure(width=10)

        self._hotspot_classified_postfix_label.configure(
            text="Postfix of Hot-spot classified image:"
        )
        self._hotspot_classified_postfix_entry.configure(width=20)

        self._hotspot_heatmap_postfix_label.configure(
            text="Postfix of Hot-spot heatmap image:"
        )
        self._hotspot_heatmap_postfix_entry.configure(width=20)

        self._floating_classified_postfix_label.configure(
            text="Postfix of Floating waste classified image:"
        )
        self._floating_classified_postfix_entry.configure(width=20)

        self._floating_heatmap_postfix_label.configure(
            text="Postfix of Floating waste heatmap image:"
        )
        self._floating_heatmap_postfix_entry.configure(width=20)

        self._floating_masked_classified_postfix_label.configure(
            text="Postfix of Floating waste masked and classified image:"
        )
        self._floating_masked_classified_postfix_entry.configure(width=20)

        self._floating_masked_heatmap_postfix_label.configure(
            text="Postfix of Floating waste masked heatmap image:"
        )
        self._floating_masked_heatmap_postfix_entry.configure(width=20)

        self._washed_up_before_postfix_label.configure(
            text="Postfix of Washed up waste first result image:"
        )
        self._washed_up_before_postfix_entry.configure(width=20)

        self._washed_up_after_postfix_label.configure(
            text="Postfix of Washed up waste second result image:"
        )
        self._washed_up_after_postfix_entry.configure(width=20)

        self._training_labels.configure(text="Training labels", padding=10)
        for i in range(9):
            self._training_labels.rowconfigure(i, weight=1)
        self._training_labels.columnconfigure(0, weight=1)

        self._training_blue.configure(text="Blue", variable=self._vars["training_blue"])
        self._training_green.configure(
            text="Green", variable=self._vars["training_green"]
        )
        self._training_red.configure(text="Red", variable=self._vars["training_red"])
        self._training_nir.configure(text="NIR", variable=self._vars["training_nir"])
        self._training_pi.configure(text="PI", variable=self._vars["training_pi"])
        self._training_ndwi.configure(text="NDWI", variable=self._vars["training_ndwi"])
        self._training_ndvi.configure(text="NDVI", variable=self._vars["training_ndvi"])
        self._training_rndvi.configure(
            text="RNDVI", variable=self._vars["training_rndvi"]
        )
        self._training_sr.configure(text="SR", variable=self._vars["training_sr"])
        self._training_apwi.configure(text="APWI", variable=self._vars["training_apwi"])

        self._color_settings.configure(text="Color settings", padding=5)
        for i in range(16):
            self._color_settings.rowconfigure(i, weight=1)
        self._color_settings.columnconfigure(0, weight=1)
        self._color_settings.columnconfigure(1, weight=1)

        for i in range(len(self._color_labels)):
            if i == 0:
                self._color_labels[i].configure(text="Background:")
            else:
                text = "Class " + str(i) + " Color:"
                self._color_labels[i].configure(text=text)
            self._color_buttons[i].configure(width=6)

        self._ok_btn.configure(text="OK")
        self._cancel_btn.configure(text="Cancel")

        self._create_tooltips()

    def _style_components(self) -> None:
        """
        Sets style of visual components.

        :return: None
        """

        self._satellite_lf["bootstyle"] = "default"

        self._planet_rb["bootstyle"] = "default"
        self._sentinel_rb["bootstyle"] = "default"

        self._sentinel_settings_lf["bootstyle"] = "default"

        self._sentinel_blue_label["bootstyle"] = "default"
        self._sentinel_blue_spinbox["bootstyle"] = "default"

        self._sentinel_green_label["bootstyle"] = "default"
        self._sentinel_green_spinbox["bootstyle"] = "default"

        self._sentinel_red_label["bootstyle"] = "default"
        self._sentinel_red_spinbox["bootstyle"] = "default"

        self._sentinel_nir_label["bootstyle"] = "default"
        self._sentinel_nir_spinbox["bootstyle"] = "default"

        self._value_settings_lf["bootstyle"] = "default"

        self._training_estimators_label["bootstyle"] = "default"
        self._training_estimators_entry["bootstyle"] = "default"

        self._morphology_matrix_label["bootstyle"] = "default"
        self._morphology_matrix_spinbox["bootstyle"] = "default"

        self._morphology_iterations_label["bootstyle"] = "default"
        self._morphology_iterations_spinbox["bootstyle"] = "default"

        self._washed_up_heatmap_sections_label["bootstyle"] = "default"
        self._washed_up_heatmap_sections_spinbox["bootstyle"] = "default"

        self._heatmap_high_label["bootstyle"] = "default"
        self._heatmap_high_spinbox["bootstyle"] = "default"

        self._heatmap_medium_label["bootstyle"] = "default"
        self._heatmap_medium_spinbox["bootstyle"] = "default"

        self._heatmap_low_label["bootstyle"] = "default"
        self._heatmap_low_spinbox["bootstyle"] = "default"

        self._c_id_frame["bootstyle"] = "default"

        self._garbage_c_id_label["bootstyle"] = "default"
        self._garbage_c_id_spinbox["bootstyle"] = "default"

        self._water_c_id_label["bootstyle"] = "default"
        self._water_c_id_spinbox["bootstyle"] = "default"

        self._paths_lf["bootstyle"] = "default"

        self._working_dir_label["bootstyle"] = "default"
        self._working_dir_entry["bootstyle"] = "default"
        self._working_dir_browse_btn["bootstyle"] = "default"

        self._hotspot_rf_label["bootstyle"] = "default"
        self._hotspot_rf_entry["bootstyle"] = "default"
        self._hotspot_rf_browse_btn["bootstyle"] = "default"

        self._floating_rf_label["bootstyle"] = "default"
        self._floating_rf_entry["bootstyle"] = "default"
        self._floating_rf_browse_btn["bootstyle"] = "default"

        self._file_settings_lf["bootstyle"] = "default"

        self._file_extension_label["bootstyle"] = "default"
        self._file_extension_entry["bootstyle"] = "default"

        self._hotspot_classified_postfix_label["bootstyle"] = "default"
        self._hotspot_classified_postfix_entry["bootstyle"] = "default"

        self._hotspot_heatmap_postfix_label["bootstyle"] = "default"
        self._hotspot_heatmap_postfix_entry["bootstyle"] = "default"

        self._floating_classified_postfix_label["bootstyle"] = "default"
        self._floating_classified_postfix_entry["bootstyle"] = "default"

        self._floating_heatmap_postfix_label["bootstyle"] = "default"
        self._floating_heatmap_postfix_entry["bootstyle"] = "default"

        self._floating_masked_classified_postfix_label["bootstyle"] = "default"
        self._floating_masked_classified_postfix_entry["bootstyle"] = "default"

        self._floating_masked_heatmap_postfix_label["bootstyle"] = "default"
        self._floating_masked_heatmap_postfix_entry["bootstyle"] = "default"

        self._washed_up_before_postfix_label["bootstyle"] = "default"
        self._washed_up_before_postfix_entry["bootstyle"] = "default"

        self._washed_up_after_postfix_label["bootstyle"] = "default"
        self._washed_up_after_postfix_entry["bootstyle"] = "default"

        self._training_labels["bootstyle"] = "default"

        self._training_blue["bootstyle"] = "default"
        self._training_green["bootstyle"] = "default"
        self._training_red["bootstyle"] = "default"
        self._training_nir["bootstyle"] = "default"
        self._training_pi["bootstyle"] = "default"
        self._training_ndwi["bootstyle"] = "default"
        self._training_ndvi["bootstyle"] = "default"
        self._training_rndvi["bootstyle"] = "default"
        self._training_sr["bootstyle"] = "default"
        self._training_apwi["bootstyle"] = "default"

        self._color_settings["bootstyle"] = "default"

        for i in range(len(self._color_labels)):
            self._color_labels[i]["bootstyle"] = "default"

        self._ok_btn["bootstyle"] = "default"
        self._cancel_btn["bootstyle"] = "secondary"

    def _place_components(self) -> None:
        """
        Places the visual components on the window.

        :return: None
        """

        self._satellite_lf.place(x=20, y=10, height=75, width=200)
        self._planet_rb.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self._sentinel_rb.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self._sentinel_settings_lf.place(x=230, y=10, height=75, width=560)

        self._sentinel_blue_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self._sentinel_blue_spinbox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self._sentinel_green_label.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        self._sentinel_green_spinbox.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        self._sentinel_red_label.grid(row=0, column=4, sticky="ew", padx=5, pady=5)
        self._sentinel_red_spinbox.grid(row=0, column=5, sticky="ew", padx=5, pady=5)

        self._sentinel_nir_label.grid(row=0, column=6, sticky="ew", padx=5, pady=5)
        self._sentinel_nir_spinbox.grid(row=0, column=7, sticky="ew", padx=5, pady=5)

        self._value_settings_lf.place(x=20, y=95, height=200, width=770)

        self._training_estimators_label.grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        self._training_estimators_entry.grid(
            row=0, column=1, sticky="ew", padx=5, pady=5
        )

        self._morphology_matrix_label.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self._morphology_matrix_spinbox.grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        self._morphology_iterations_label.grid(
            row=2, column=0, sticky="ew", padx=5, pady=5
        )
        self._morphology_iterations_spinbox.grid(
            row=2, column=1, sticky="ew", padx=5, pady=5
        )

        self._washed_up_heatmap_sections_label.grid(
            row=3, column=0, sticky="ew", padx=5, pady=5
        )
        self._washed_up_heatmap_sections_spinbox.grid(
            row=3, column=1, sticky="ew", padx=5, pady=5
        )

        self._heatmap_high_label.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        self._heatmap_high_spinbox.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        self._heatmap_medium_label.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
        self._heatmap_medium_spinbox.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        self._heatmap_low_label.grid(row=2, column=2, sticky="ew", padx=5, pady=5)
        self._heatmap_low_spinbox.grid(row=2, column=3, sticky="ew", padx=5, pady=5)

        self._c_id_frame.grid(
            row=3, column=2, columnspan=2, sticky="nsew", padx=5, pady=5
        )

        self._garbage_c_id_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self._garbage_c_id_spinbox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self._water_c_id_label.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        self._water_c_id_spinbox.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        self._paths_lf.place(x=20, y=305, height=150, width=880)

        self._working_dir_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self._working_dir_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self._working_dir_browse_btn.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        self._hotspot_rf_label.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self._hotspot_rf_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self._hotspot_rf_browse_btn.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        self._floating_rf_label.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self._floating_rf_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self._floating_rf_browse_btn.grid(row=2, column=2, sticky="ew", padx=5, pady=5)

        self._file_settings_lf.place(x=20, y=465, height=250, width=880)

        self._file_extension_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self._file_extension_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self._hotspot_classified_postfix_label.grid(
            row=1, column=0, sticky="ew", padx=5, pady=5
        )
        self._hotspot_classified_postfix_entry.grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        self._hotspot_heatmap_postfix_label.grid(
            row=2, column=0, sticky="ew", padx=5, pady=5
        )
        self._hotspot_heatmap_postfix_entry.grid(
            row=2, column=1, sticky="ew", padx=5, pady=5
        )

        self._floating_classified_postfix_label.grid(
            row=3, column=0, sticky="ew", padx=5, pady=5
        )
        self._floating_classified_postfix_entry.grid(
            row=3, column=1, sticky="ew", padx=5, pady=5
        )

        self._floating_heatmap_postfix_label.grid(
            row=4, column=0, sticky="ew", padx=5, pady=5
        )
        self._floating_heatmap_postfix_entry.grid(
            row=4, column=1, sticky="ew", padx=5, pady=5
        )

        self._floating_masked_classified_postfix_label.grid(
            row=0, column=2, sticky="ew", padx=5, pady=5
        )
        self._floating_masked_classified_postfix_entry.grid(
            row=0, column=3, sticky="ew", padx=5, pady=5
        )

        self._floating_masked_heatmap_postfix_label.grid(
            row=1, column=2, sticky="ew", padx=5, pady=5
        )
        self._floating_masked_heatmap_postfix_entry.grid(
            row=1, column=3, sticky="ew", padx=5, pady=5
        )

        self._washed_up_before_postfix_label.grid(
            row=2, column=2, sticky="ew", padx=5, pady=5
        )
        self._washed_up_before_postfix_entry.grid(
            row=2, column=3, sticky="ew", padx=5, pady=5
        )

        self._washed_up_after_postfix_label.grid(
            row=3, column=2, sticky="ew", padx=5, pady=5
        )
        self._washed_up_after_postfix_entry.grid(
            row=3, column=3, sticky="ew", padx=5, pady=5
        )

        self._training_labels.place(x=800, y=10, height=285, width=100)

        self._training_blue.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self._training_green.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self._training_red.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self._training_nir.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self._training_pi.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        self._training_ndwi.grid(row=5, column=0, sticky="nsew", padx=5, pady=5)
        self._training_ndvi.grid(row=6, column=0, sticky="nsew", padx=5, pady=5)
        self._training_rndvi.grid(row=7, column=0, sticky="nsew", padx=5, pady=5)
        self._training_sr.grid(row=8, column=0, sticky="nsew", padx=5, pady=5)
        self._training_apwi.grid(row=9, column=0, sticky="nsew", padx=5, pady=5)

        self._color_settings.place(x=910, y=10, height=655, width=160)

        for i in range(len(self._color_labels)):
            self._color_labels[i].grid(row=i, column=0, sticky="ew", padx=5, pady=5)
            self._color_buttons[i].grid(row=i, column=1, sticky="e", padx=5, pady=5)

        self._ok_btn.place(x=995, y=685, height=30, width=70)
        self._cancel_btn.place(x=920, y=685, height=30, width=70)

    def _setup_vars(self) -> None:
        """
        Initializes the ttk.Variables of this class.

        :return: None
        """

        self._vars = dict()
        self._vars["satellite_rb"] = ttk.IntVar(master=self)
        self._vars["training_blue"] = ttk.IntVar(master=self)
        self._vars["training_green"] = ttk.IntVar(master=self)
        self._vars["training_red"] = ttk.IntVar(master=self)
        self._vars["training_nir"] = ttk.IntVar(master=self)
        self._vars["training_pi"] = ttk.IntVar(master=self)
        self._vars["training_ndwi"] = ttk.IntVar(master=self)
        self._vars["training_ndvi"] = ttk.IntVar(master=self)
        self._vars["training_rndvi"] = ttk.IntVar(master=self)
        self._vars["training_sr"] = ttk.IntVar(master=self)
        self._vars["training_apwi"] = ttk.IntVar(master=self)

    def _create_tooltips(self) -> None:
        """
        Creates the tooltips for all labels.

        :return: None
        """

        # Satellite type
        ToolTip(self._satellite_lf, "The type of satellite that recorded the image.")

        # Sentinel-2 settings
        ToolTip(
            self._sentinel_blue_label,
            "The index of the Blue band on the Sentinel-2 image.",
        )
        ToolTip(
            self._sentinel_green_label,
            "The index of the Green band on the Sentinel-2 image.",
        )
        ToolTip(
            self._sentinel_red_label,
            "The index of the Red band on the Sentinel-2 image.",
        )
        ToolTip(
            self._sentinel_nir_label,
            "The index of the NIR (Near-infrared) band on the Sentinel-2 image.",
        )

        # Algorithm settings
        ToolTip(self._training_estimators_label, "The number of trees in the forest.")
        ToolTip(
            self._morphology_matrix_label,
            "Size of the kernel matrix for the morphology algorithms.",
        )
        ToolTip(
            self._morphology_iterations_label,
            "Number of iterations for the morphology algorithms.",
        )
        ToolTip(
            self._washed_up_heatmap_sections_label,
            "The larger the number, the more unique "
            "pixels are visible on result images.",
        )

        for label in [
            self._heatmap_high_label,
            self._heatmap_medium_label,
            self._heatmap_low_label,
        ]:
            ToolTip(
                label,
                "This value is used by the Hot-spot and Floating waste"
                " detection methods. On heatmap images there are four"
                " colors: red, yellow, green and black. The colors are"
                " decided by the classifier's prediction confidence:\n\n"
                "red\t--> High probability <= confidence <= 100%\n\n"
                "yellow\t--> Medium probability <= confidence "
                "< High probability\n\n"
                "green\t--> Low probability <= confidence "
                "< Medium probability\n\n"
                "black\t--> otherwise.",
            )
        ToolTip(
            self._garbage_c_id_label,
            "The Class ID of the Garbage class"
            " in the loaded Random Forest classifiers.",
        )
        ToolTip(
            self._water_c_id_label,
            "The Class ID of the Water class"
            " in the loaded Random Forest classifiers.",
        )

        # Path settings
        ToolTip(
            self._working_dir_label,
            "The working directory of the application. "
            "The result images will be saved here.",
        )
        ToolTip(
            self._hotspot_rf_label,
            "The path of the saved Random Forest classifier model "
            "for the Hot-spot detection method.",
        )
        ToolTip(
            self._floating_rf_label,
            "The path of the saved Random Forest classifier model "
            "for the Floating waste detection method.",
        )
        ToolTip(self._working_dir_browse_btn, "Browse working directory.")
        ToolTip(
            self._hotspot_rf_browse_btn,
            "Browse saved Random Forest classifier model "
            "for the Hot-spot detection method.",
        )
        ToolTip(
            self._floating_rf_browse_btn,
            "Browse saved Random Forest classifier model "
            "for the Floating waste detection method.",
        )

        # Output file settings
        ToolTip(
            self._file_extension_label,
            "File extension of the saved images. Recommended: tif.",
        )
        ToolTip(
            self._hotspot_classified_postfix_label,
            "File name postfix of the classified" " images (Hot-spot detection).",
        )
        ToolTip(
            self._hotspot_heatmap_postfix_label,
            "File name postfix of the heatmap" " images (Hot-spot detection).",
        )
        ToolTip(
            self._floating_classified_postfix_label,
            "File name postfix of the classified" " images (Floating waste detection).",
        )
        ToolTip(
            self._floating_heatmap_postfix_label,
            "File name postfix of the heatmap" " images (Floating waste detection).",
        )
        ToolTip(
            self._floating_masked_classified_postfix_label,
            "File name postfix of the masked"
            " and classified images "
            "(Floating waste detection).",
        )
        ToolTip(
            self._floating_masked_heatmap_postfix_label,
            "File name postfix of the masked"
            " heatmap images "
            "(Floating waste detection).",
        )
        ToolTip(
            self._washed_up_before_postfix_label,
            "File name postfix of the first result"
            " image (Washed up waste detection).",
        )
        ToolTip(
            self._washed_up_after_postfix_label,
            "File name postfix of the second result"
            " image (Washed up waste detection).",
        )

        # Training labels
        ToolTip(self._training_blue, "Blue band.")
        ToolTip(self._training_green, "Green band.")
        ToolTip(self._training_red, "Red band.")
        ToolTip(self._training_nir, "NIR (Near-infrared) band.")
        ToolTip(self._training_pi, "Plastic index: (NIR) / (NIR + Red).")
        ToolTip(
            self._training_ndwi,
            "Normalized Difference Water index: " "(Green - NIR) / (Green + NIR).",
        )
        ToolTip(
            self._training_ndvi,
            "Normalized Difference Vegetation index: " "(NIR - Red) / (NIR + Red).",
        )
        ToolTip(
            self._training_rndvi,
            "Reversed Normalized Difference Vegetation index: "
            "(Red - NIR) / (Red + NIR).",
        )
        ToolTip(self._training_sr, "Simple Ratio: (NIR) / (Red).")
        ToolTip(
            self._training_apwi,
            "Agricultural Plastic Waste Index: (Blue) / (1 - (Red + Green + NIR) / 3).",
        )

        # Color settings
        for btn in self._color_buttons:
            ToolTip(btn, " Choose color.")
