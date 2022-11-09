import os
import view
import math
from model import model
import traceback
import threading
import numpy as np
import tkinter as tk
import tkinter.messagebox
import ttkbootstrap as ttk

from osgeo import gdal
from model.exceptions import *
from tkinter import filedialog as fd
from ttkbootstrap.constants import *
from matplotlib.figure import Figure
from typing import Union, List, TextIO, Tuple, Set
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog



MAX_PIXEL_COUNT = 40000000


class Controller(object):
    """
    A class for controlling this application.

    """

    def __init__(self, view_instance: view.View, model_instance: model.Model) -> None:
        """
        The constructor of the Controller class.

        :param view_instance: an instance of the View class
        :param model_instance: an instance of the Model class
        """

        self._view = view_instance
        self._model = model_instance

        self._bind_commands()

    # Non-static public methods
    def mainloop(self) -> None:
        """
        Starts the mainloop of the application.

        :return: None
        """

        self._settings_show()
        self._settings_on_ok()
        self._view.show()

    # Non-static protected methods
    def _register_validator_functions(self) -> None:
        """
        Registers the validator functions for TrainingView and SettingsView.

        :return: None
        """

        self._sentinel_func = self._view.settings_view.register(Controller._validate_sentinel_band)
        self._decision_tree_func = self._view.settings_view.register(Controller._validate_decision_tree_number)
        self._morphology_func = self._view.settings_view.register(Controller._validate_morphology)
        self._heatmap_func = self._view.settings_view.register(Controller._validate_heatmap)
        self._settings_mc_id_func = self._view.settings_view.register(Controller._validate_settings_mc_id)
        self._heatmap_section_func = self._view.settings_view.register(Controller._validate_heatmap_sections)
        self._working_dir_func = self._view.settings_view.register(Controller._validate_working_dir)
        self._file_path_func = self._view.settings_view.register(Controller._validate_file_path)
        self._file_extension_func = self._view.settings_view.register(Controller._validate_file_extension)
        self._postfix_func = self._view.settings_view.register(Controller._validate_postfix)
        self._alpha_func = self._view.training_view.register(Controller._validate_alpha)
        self._training_mc_id_func = self._view.training_view.register(Controller._validate_training_mc_id)

    def _register_invalidator_functions(self) -> None:
        """
        Registers the functions for invalid inputs in TrainingView and SettingsView.

        :return: None
        """

        self._invalid_sentinel_band_func = self._view.settings_view.register(self._invalid_sentinel_band)
        self._invalid_decision_tree_number_func = \
            self._view.settings_view.register(self._invalid_decision_tree_number)
        self._invalid_morphology_func = self._view.settings_view.register(self._invalid_morphology)
        self._invalid_iterations_func = self._view.settings_view.register(self._invalid_iterations)
        self._invalid_heatmap_sections_func = self._view.settings_view.register(self._invalid_heatmap_sections)
        self._invalid_heatmap_func = self._view.settings_view.register(self._invalid_heatmap)
        self._invalid_settings_mc_id_func = self._view.settings_view.register(self._invalid_settings_mc_id)
        self._invalid_working_dir_func = self._view.settings_view.register(self._invalid_working_dir)
        self._invalid_file_path_func = self._view.settings_view.register(self._invalid_file_path)
        self._invalid_file_extension_func = self._view.settings_view.register(self._invalid_file_extension)
        self._invalid_postfix_func = self._view.settings_view.register(self._invalid_postfix)

    def _view_bind_commands(self) -> None:
        """
        Binds the commands to the widgets in View.

        :return: None
        """

        self._view.add_files_btn.configure(command=self._view_open_files)
        self._view.delete_files_btn.configure(command=self._view_delete_files)
        self._view.start_process_btn.configure(command=self._view_start_processing_on_separate_thread)
        self._view.train_rf_btn.configure(command=self._view_open_train_rf_window)
        self._view.coord_btn.configure(command=self._view_save_coords)
        self._view.estimate_area_btn.configure(command=self._view_estimate_garbage_area)
        self._view.menubar.add_command(label="Settings", command=self._settings_show)
        self._view.menubar.add_command(label="About", command=self._show_about)

        self._view.opened_files_lb.bind("<<ListboxSelect>>", self._view_listbox_item_selected)
        self._view.left_canvas.canvas.bind("<ButtonPress-3>", self._view_left_canvas_move_from)
        self._view.left_canvas.canvas.bind("<B3-Motion>", self._view_left_canvas_move_to)
        self._view.left_canvas.canvas.bind("<MouseWheel>", self._view_left_canvas_wheel)
        self._view.right_canvas.canvas.bind("<ButtonPress-3>", self._view_right_canvas_move_from)
        self._view.right_canvas.canvas.bind("<B3-Motion>", self._view_right_canvas_move_to)
        self._view.right_canvas.canvas.bind("<MouseWheel>", self._view_right_canvas_wheel)

        self._view.vars["process_menu"].trace("w", lambda name, index, mode, sv=self._view.vars["process_menu"]:
        self._view_change_process_btn_text())
        self._view.vars["heatmap_toggle"].trace("w", lambda name, index, mode, sv=self._view.vars["heatmap_toggle"]:
        self._view_toggle_heatmap())
        self._view.vars["heatmap_high"].trace("w", lambda name, index, mode, sv=self._view.vars["heatmap_high"]:
        self._view_toggle_heatmap())
        self._view.vars["heatmap_medium"].trace("w", lambda name, index, mode, sv=self._view.vars["heatmap_medium"]:
        self._view_toggle_heatmap())
        self._view.vars["heatmap_low"].trace("w", lambda name, index, mode, sv=self._view.vars["heatmap_low"]:
        self._view_toggle_heatmap())

    def _settings_bind_commands(self) -> None:
        """
        Binds the commands to the widgets in SettingsView.

        :return: None
        """

        for i in range(len(self._view.settings_view.color_buttons)):
            self._view.settings_view.color_buttons[i].configure(
                command=lambda b=self._view.settings_view.color_buttons[i]: self._settings_color_btn_clicked(b))

        self._view.settings_view.sentinel_blue_spinbox.configure(validate="focusout",
                                                                 validatecommand=(self._sentinel_func, "%P"),
                                                                 invalidcommand=self._invalid_sentinel_band_func)

        self._view.settings_view.sentinel_green_spinbox.configure(validate="focusout",
                                                                  validatecommand=(self._sentinel_func, "%P"),
                                                                  invalidcommand=self._invalid_sentinel_band_func)

        self._view.settings_view.sentinel_red_spinbox.configure(validate="focusout",
                                                                validatecommand=(self._sentinel_func, "%P"),
                                                                invalidcommand=self._invalid_sentinel_band_func)

        self._view.settings_view.sentinel_nir_spinbox.configure(validate="focusout",
                                                                validatecommand=(self._sentinel_func, "%P"),
                                                                invalidcommand=self._invalid_sentinel_band_func)

        self._view.settings_view.training_estimators_entry.configure(
            validate="focusout",
            validatecommand=(self._decision_tree_func, "%P"),
            invalidcommand=self._invalid_decision_tree_number_func
        )

        self._view.settings_view.morphology_matrix_spinbox.configure(validate="focusout",
                                                                     validatecommand=(self._morphology_func, "%P"),
                                                                     invalidcommand=self._invalid_morphology_func)

        self._view.settings_view.morphology_iterations_spinbox.configure(validate="focusout",
                                                                         validatecommand=(self._morphology_func, "%P"),
                                                                         invalidcommand=self._invalid_morphology_func)

        self._view.settings_view.washed_up_heatmap_sections_spinbox.configure(
            validate="focusout",
            validatecommand=(self._heatmap_section_func, "%P"),
            invalidcommand=self._invalid_heatmap_sections_func)

        self._view.settings_view.heatmap_high_spinbox.configure(validate="focusout",
                                                                validatecommand=(self._heatmap_func, "%P"),
                                                                invalidcommand=self._invalid_heatmap_func)

        self._view.settings_view.heatmap_medium_spinbox.configure(validate="focusout",
                                                                  validatecommand=(self._heatmap_func, "%P"),
                                                                  invalidcommand=self._invalid_heatmap_func)

        self._view.settings_view.heatmap_low_spinbox.configure(validate="focusout",
                                                               validatecommand=(self._heatmap_func, "%P"),
                                                               invalidcommand=self._invalid_heatmap_func)

        self._view.settings_view.garbage_mc_id_spinbox.configure(validate="focusout",
                                                                 validatecommand=(self._settings_mc_id_func, "%P"),
                                                                 invalidcommand=self._invalid_settings_mc_id_func)

        self._view.settings_view.water_mc_id_spinbox.configure(validate="focusout",
                                                               validatecommand=(self._settings_mc_id_func, "%P"),
                                                               invalidcommand=self._invalid_settings_mc_id_func)

        self._view.settings_view.working_dir_entry.configure(validate="focusout",
                                                             validatecommand=(self._working_dir_func, "%P"),
                                                             invalidcommand=self._invalid_working_dir_func)

        self._view.settings_view.hotspot_rf_entry.configure(validate="focusout",
                                                            validatecommand=(self._file_path_func, "%P"),
                                                            invalidcommand=self._invalid_file_path_func)

        self._view.settings_view.floating_rf_entry.configure(validate="focusout",
                                                             validatecommand=(self._file_path_func, "%P"),
                                                             invalidcommand=self._invalid_file_path_func)

        self._view.settings_view.file_extension_entry.configure(validate="focusout",
                                                                validatecommand=(self._file_extension_func, "%P"),
                                                                invalidcommand=self._invalid_file_extension_func)

        self._view.settings_view.hotspot_classified_postfix_entry.configure(validate="focusout",
                                                                            validatecommand=(self._postfix_func, "%P"),
                                                                            invalidcommand=self._invalid_postfix_func)

        self._view.settings_view.hotspot_heatmap_postfix_entry.configure(validate="focusout",
                                                                         validatecommand=(self._postfix_func, "%P"),
                                                                         invalidcommand=self._invalid_postfix_func)

        self._view.settings_view.floating_classified_postfix_entry.configure(validate="focusout",
                                                                             validatecommand=(self._postfix_func, "%P"),
                                                                             invalidcommand=self._invalid_postfix_func)

        self._view.settings_view.floating_heatmap_postfix_entry.configure(validate="focusout",
                                                                          validatecommand=(self._postfix_func, "%P"),
                                                                          invalidcommand=self._invalid_postfix_func)

        self._view.settings_view.floating_masked_classified_postfix_entry.configure(
            validate="focusout",
            validatecommand=(self._postfix_func, "%P"),
            invalidcommand=self._invalid_postfix_func)

        self._view.settings_view.floating_masked_heatmap_postfix_entry.configure(
            validate="focusout",
            validatecommand=(self._postfix_func, "%P"),
            invalidcommand=self._invalid_postfix_func)

        self._view.settings_view.washed_up_before_postfix_entry.configure(validate="focusout",
                                                                          validatecommand=(self._postfix_func, "%P"),
                                                                          invalidcommand=self._invalid_postfix_func)

        self._view.settings_view.washed_up_after_postfix_entry.configure(validate="focusout",
                                                                         validatecommand=(self._postfix_func, "%P"),
                                                                         invalidcommand=self._invalid_postfix_func)

        self._view.settings_view.working_dir_browse_btn.configure(command=self._settings_working_dir_browse_directory)
        self._view.settings_view.hotspot_rf_browse_btn.configure(command=lambda b="hotspot":
                                                                 self._settings_browse_file(b))
        self._view.settings_view.floating_rf_browse_btn.configure(command=lambda b="floating":
                                                                  self._settings_browse_file(b))
        self._view.settings_view.ok_btn.configure(command=self._settings_on_ok)
        self._view.settings_view.cancel_btn.configure(command=self._view.settings_view.hide)

        self._view.settings_view.protocol("WM_DELETE_WINDOW", self._view.settings_view.hide)

    def _training_bind_commands(self) -> None:
        """
        Binds the commands to the widgets in TrainingView.

        :return: None
        """

        self._view.training_view.load_csv_btn.configure(command=self._training_load_csv)
        self._view.training_view.back_btn.configure(command=self._training_on_closing)
        self._view.training_view.open_input_img_btn.configure(command=self._training_open_files)
        self._view.training_view.delete_input_img_btn.configure(command=self._training_delete_files)
        self._view.training_view.add_btn.configure(command=self._training_add_new)
        self._view.training_view.delete_btn.configure(command=self._training_delete)
        self._view.training_view.training_btn.configure(command=self._training_start_on_separate_thread)
        self._view.training_view.color_btn.configure(command=self._training_change_color_btn_color)

        self._view.training_view.mc_input.configure(validate="all", validatecommand=(self._alpha_func, "%P"))
        self._view.training_view.mc_spinbox.configure(validate="all", validatecommand=(self._training_mc_id_func, "%P"))

        self._view.training_view.zoom_canvas.canvas.bind("<ButtonPress-1>", self._training_place_point_on_canvas)
        self._view.training_view.zoom_canvas.canvas.bind("<ButtonPress-2>", self._training_place_polygon_on_canvas)
        self._view.training_view.zoom_canvas.canvas.bind("<ButtonPress-3>", self._training_canvas_move_from)
        self._view.training_view.zoom_canvas.canvas.bind("<B3-Motion>", self._training_canvas_move_to)
        self._view.training_view.zoom_canvas.canvas.bind("<MouseWheel>", self._training_canvas_wheel)

        self._view.training_view.treeview.bind("<<TreeviewSelect>>", self._training_treeview_item_selected)
        self._view.training_view.treeview.bind("<Motion>", lambda event: "break")
        self._view.training_view.treeview.bind("<Button-1>", self._training_disable_treeview_column_resizing)
        self._view.training_view.treeview.bind("<Double-Button-1>", lambda event: "break")
        self._view.training_view.treeview.bind("<Key>", lambda event: "break")
        self._view.training_view.treeview.bind("<Return>", lambda event: "break")
        self._view.training_view.opened_files_lb.bind("<<ListboxSelect>>", self._training_listbox_item_selected)

        self._view.training_view.protocol("WM_DELETE_WINDOW", self._training_on_closing)

    def _bind_commands(self) -> None:
        """
        Sets the event handler and validation methods of the visual components.

        :return: None
        """

        self._register_validator_functions()
        self._register_invalidator_functions()

        self._view_bind_commands()
        self._settings_bind_commands()
        self._training_bind_commands()

    def _view_change_process_btn_text(self) -> None:
        """
        Changes the Process label in View.

        :return: None
        """

        text_var = self._view.vars["process_menu"].get()

        if text_var == 1:
            self._view.process_btn.configure(text="Hot-spot detection")
        elif text_var == 2:
            self._view.process_btn.configure(text="Floating waste detection")
        elif text_var == 3:
            self._view.process_btn.configure(text="Washed up waste detection")

        self._view_update_start_process_btn_state()

    def _view_toggle_heatmap(self) -> None:
        """
        Displays or hides the heatmap.

        :return: None
        """

        toggle_var = self._view.vars["heatmap_toggle"].get()
        low_var = self._view.vars["heatmap_low"].get()
        medium_var = self._view.vars["heatmap_medium"].get()
        high_var = self._view.vars["heatmap_high"].get()

        view_selected_files = self._view.get_curselection_values_listbox()

        heatmap_color = list()
        if low_var == 1:
            heatmap_color.append("low")
        if medium_var == 1:
            heatmap_color.append("medium")
        if high_var == 1:
            heatmap_color.append("high")

        satellite_rgb = self._get_satellite_rgb()

        model_source_files, model_result_files = self._model_get_source_and_result_files()
        if len(view_selected_files) == 1:
            selected_file = view_selected_files[0]

            if selected_file in model_source_files:
                index = model_source_files.index(selected_file)
                classification = model_result_files[index][0]
                heatmap = model_result_files[index][1]

                if toggle_var == 0:
                    self._view.show_image_on_canvas(
                        canvas_name="right",
                        img_or_array=classification,
                        image_type="classified",
                        satellite_rgb=satellite_rgb,
                        color_map=self._model.get_classification_color_map(classification)
                    )
                    self._view.right_img_lf.configure(text="Classified image")
                elif toggle_var == 1:
                    self._view.show_image_on_canvas(
                        canvas_name="right",
                        img_or_array=heatmap,
                        image_type="heatmap",
                        satellite_rgb=satellite_rgb,
                        color_map=self._model.get_heatmap_color_map(heatmap, heatmap_color)
                    )
                    self._view.right_img_lf.configure(text="Heatmap image")
            else:
                self._view.clear_canvas("right")
        elif len(view_selected_files) == 2:
            selected_file_1 = view_selected_files[0]
            selected_file_2 = view_selected_files[1]

            if (selected_file_1, selected_file_2) in model_source_files:
                index = model_source_files.index((selected_file_1, selected_file_2))
                before, after = model_result_files[index]

                if toggle_var == 0:
                    self._view.show_image_on_canvas(
                        canvas_name="left",
                        img_or_array=selected_file_1,
                        image_type="rgb",
                        satellite_rgb=satellite_rgb
                    )
                    self._view.left_img_lf.configure(text="Source image 1")

                    self._view.show_image_on_canvas(
                        canvas_name="right",
                        img_or_array=selected_file_2,
                        image_type="rgb",
                        satellite_rgb=satellite_rgb
                    )
                    self._view.right_img_lf.configure(text="Source image 2")
                elif toggle_var == 1:
                    self._view.show_image_on_canvas(
                        canvas_name="left",
                        img_or_array=before,
                        image_type="heatmap",
                        satellite_rgb=satellite_rgb,
                        color_map=self._model.get_heatmap_color_map(before, heatmap_color)
                    )
                    self._view.left_img_lf.configure(text="Result image 1")

                    self._view.show_image_on_canvas(
                        canvas_name="right",
                        img_or_array=after,
                        image_type="heatmap",
                        satellite_rgb=satellite_rgb,
                        color_map=self._model.get_heatmap_color_map(after, heatmap_color)
                    )
                    self._view.right_img_lf.configure(text="Result image 2")
            else:
                self._view.clear_canvas("left")
                self._view.clear_canvas("right")

    def _view_open_files(self) -> None:
        """
        Handles the file opening.

        :return: None
        """

        new_files = self._open_files()

        if not new_files:
            return

        not_valid_band = list()
        not_valid_size = list()
        not_valid_extension = list()

        for file in new_files:
            name, extension = os.path.splitext(file)
            if extension != ".tif":
                not_valid_extension.append(file)
                continue
            try:
                dataset = gdal.Open(file, gdal.GA_ReadOnly)
                rows = dataset.RasterYSize
                cols = dataset.RasterXSize

                if dataset.RasterCount < 4:
                    not_valid_band.append(file)
                elif rows * cols > MAX_PIXEL_COUNT:
                    not_valid_size.append(file)
            finally:
                del dataset

        if not_valid_band:
            tkinter.messagebox.showerror(
                parent=self._view.opened_files_lb,
                title="File opening",
                message="There were files with not enough bands! These were not added."
            )

            for file in not_valid_band:
                new_files.remove(file)

        if not_valid_size:
            tkinter.messagebox.showerror(
                parent=self._view.opened_files_lb,
                title="File opening",
                message="There were too large images! The limit is " + str(MAX_PIXEL_COUNT) + " pixels. "
                                                                                              "These were not added."
            )

            for file in not_valid_size:
                new_files.remove(file)

        if not_valid_extension:
            tkinter.messagebox.showerror(
                parent=self._view.opened_files_lb,
                title="File opening",
                message="There were images with extension other than .tif! These were not added."
            )

            for file in not_valid_extension:
                new_files.remove(file)

        self._model.add_files(new_files, self._view_insert_file_into_listbox)

        self._view_update_start_process_btn_state()

    def _view_insert_file_into_listbox(self, file: str) -> None:
        """
        Handles the insertions in the listbox in View.

        :param file: path of the file
        :return: None
        """

        self._view.add_file_to_listbox(file)

    def _view_delete_files(self) -> None:
        """
        Handles the file deletion from View and Model.

        :return: None
        """

        selected_indices = self._view.get_curselection_indices_listbox()
        selected_files = self._view.get_curselection_values_listbox()

        self._model.delete_files(selected_files)
        for index in selected_indices[::-1]:
            self._view_remove_file_from_listbox(index)

        self._view_update_start_process_btn_state()

        self._view_clear_canvases()

    def _view_clear_canvases(self) -> None:
        """
        Clears the canvases in View.

        :return: None
        """

        self._view.clear_canvas(canvas_name="left")
        self._view.clear_canvas(canvas_name="right")

    def _view_remove_file_from_listbox(self, file_index: int) -> None:
        """
        Removes the specified file from View listbox.

        :param file_index: index of the file to be deleted
        :return: None
        """

        self._view.remove_file_from_listbox(file_index)

    def _view_start_processing_on_separate_thread(self) -> None:
        """
        Start the waste detection process on a separate thread.

        :return: None
        """

        if not self._settings_validate_all():
            tkinter.messagebox.showerror("Settings error", "There are values wrongly set in Settings!",
                                         parent=self._view)
            return

        process_thread = threading.Thread(target=self._view_start_processing, daemon=True)
        process_thread.start()

    def _view_start_processing(self) -> None:
        """
        Starts the selected process.

        :return: None
        """

        try:
            self._view.process_pb.configure(mode="indeterminate")
            self._view.process_pb.start(25)
            self._view_clear_canvases()
            Controller._disable_all_children(self._view)
            self._view.left_img_lf.configure(text="")
            self._view.right_img_lf.configure(text="")
            self._view.update()

            process_id = self._view.vars["process_menu"].get()
            were_wrong_labels, were_wrong_pictures = self._model.processing(process_id)

            if were_wrong_labels and process_id == 3:
                parent = self._view.get_active_window()
                tkinter.messagebox.showerror(
                    parent=parent,
                    title="Error",
                    message="There were images with no geographical intersection or "
                            "the Training labels are set wrongly in Settings!"
                )
            elif were_wrong_labels:
                parent = self._view.get_active_window()
                tkinter.messagebox.showerror(
                    parent=parent,
                    title="Error",
                    message="The Training labels are set wrongly in Settings!"
                )
            if were_wrong_pictures:
                parent = self._view.get_active_window()
                tkinter.messagebox.showerror(
                    parent=parent,
                    title="Error",
                    message="There were non-existing pictures added!"
                )
        except HotspotRandomForestFileException:
            tkinter.messagebox.showerror(
                parent=self._view,
                message="Could not load Random Forest for Hot-spot detection!"
            )
        except FloatingRandomForestFileException:
            tkinter.messagebox.showerror(
                parent=self._view,
                message="Could not load Random Forest for Floating waste detection!\nLoading previous classifier!"
            )
        except Exception as exc:
            message = traceback.format_exception_only(type(exc), exc)[0]
            if len(message) == 0:
                message = traceback.format_exc()
            tkinter.messagebox.showerror(
                title="Error",
                message=message
            )
        finally:
            self._enable_all_children(self._view)
            self._view.process_pb.stop()
            self._view.process_pb.configure(value=0, mode="determinate")

    def _view_change_start_process_btn_state(self, active: bool) -> None:
        """
        Activates or disables the Start processing button.

        :param active: True or False
        :return: None
        """

        self._view.change_start_process_btn_state(active)

    def _view_update_start_process_btn_state(self) -> None:
        """
        Updates the status of the Start processing button.

        :return: None
        """

        process_id = self._view.vars["process_menu"].get()
        listbox_size = self._view.opened_files_lb.size()

        if (process_id == 1 or process_id == 2) and not (listbox_size == 0):
            self._view_change_start_process_btn_state(active=True)
        elif process_id == 3 and listbox_size > 1:
            self._view_change_start_process_btn_state(active=True)
        else:
            self._view_change_start_process_btn_state(active=False)

    def _view_save_coords(self) -> None:
        """
        Handles the saving of garbage area to GeoJSON file.

        :return: None
        """

        toggle_var = self._view.vars["heatmap_toggle"].get()
        low_var = self._view.vars["heatmap_low"].get()
        medium_var = self._view.vars["heatmap_medium"].get()
        high_var = self._view.vars["heatmap_high"].get()

        view_selected_files = self._view.get_curselection_values_listbox()

        if len(view_selected_files) == 1:
            selected_file = view_selected_files[0]
            model_source_files, model_result_files = self._model_get_source_and_result_files()

            if selected_file in model_source_files:
                index = model_source_files.index(selected_file)
                classification = model_result_files[index][0]
                heatmap = model_result_files[index][1]

                if toggle_var:
                    search_values = list()
                    if low_var:
                        search_values.append(1)
                    if medium_var:
                        search_values.append(2)
                    if high_var:
                        search_values.append(3)

                    file = self._save_file("geojson")
                    if file:
                        self._model.create_garbage_bbox_geojson(heatmap, file, search_values)
                        file.close()

                else:
                    file = self._save_file("geojson")
                    if file:
                        self._model.create_garbage_bbox_geojson(classification, file, [100])
                        file.close()

    def _view_estimate_garbage_area(self) -> None:
        """
        Estimates the extension of the garbage area, creates plots.

        :return: None
        """

        view_selected_files = self._view.get_curselection_values_listbox()
        file_count = len(view_selected_files)

        if file_count == 0:
            return

        model_source_files, model_result_files = self._model_get_source_and_result_files()

        if 1 <= file_count <= 9:
            rows = math.ceil(file_count / 3)
            cols = file_count % 3 if file_count < 3 else 3

            can_show = False

            figure = Figure(constrained_layout=True)

            for i in range(len(view_selected_files)):
                if view_selected_files[i] in model_source_files:
                    can_show = True
                    index = model_source_files.index(view_selected_files[i])
                    classification = model_result_files[index][0]
                    heatmap = model_result_files[index][1]

                    garbage_c_id = self._model.persistence.garbage_mc_id
                    classified_area = model.Model.estimate_garbage_area(classification, "classified", garbage_c_id)
                    low_area = model.Model.estimate_garbage_area(heatmap, "heatmap", garbage_c_id, (True, False, False))
                    medium_area = model.Model.estimate_garbage_area(heatmap, "heatmap", garbage_c_id, (False, True, False))
                    high_area = model.Model.estimate_garbage_area(heatmap, "heatmap", garbage_c_id, (False, False, True))
                    values = [classified_area, low_area, medium_area, high_area]

                    if all([not (val is None) for val in values]):
                        labels = ["classified", "low", "medium", "high"]
                        positions = [i + 1 for i in range(len(values))]
                        colors = ["blue", "green", "orange", "red"]
                        width = 0.5

                        plot = figure.add_subplot(rows, cols, i + 1)
                        vals = plot.bar(positions, [val / 1000 for val in values], tick_label=labels,
                                        width=width, color=colors)
                        plot.bar_label(vals, padding=3)
                        plot.set_ymargin(0.125)
                        x_label_prefix = "..." if len(view_selected_files[i]) > 50 else ""
                        plot.set_xlabel(x_label_prefix + view_selected_files[i][-50:])
                        plot.set_ylabel("Area - m2 * 1000")

            if can_show:
                plot_window = ttk.Toplevel(master=self._view)
                plot_window.title("Estimation of garbage area")
                geometry_width = int(round(1600 / 3 * cols))
                geometry_height = int(round(900 / 3 * rows))
                plot_window.geometry(str(geometry_width) + "x" + str(geometry_height))
                plot_window.minsize(geometry_width, geometry_height)
                plot_window.place_window_center()

                canvas = FigureCanvasTkAgg(figure, master=plot_window)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
        elif file_count > 9:
            tkinter.messagebox.showerror(
                parent=self._view,
                title="Error",
                message="Too many images selected!"
            )

    def _view_open_train_rf_window(self) -> None:
        """
        Opens the TrainingView.

        :return: None
        """

        self._view.withdraw()
        self._view.training_view.show()

    def _view_listbox_item_selected(self, event) -> None:
        """
        Handles the listbox item selected event in View.

        :param event: event parameter
        :return: None
        """

        process_id = self._view.vars["process_menu"].get()
        self._view.vars["heatmap_toggle"].set(0)

        view_selected_files = self._view.get_curselection_values_listbox()

        satellite_rgb = self._get_satellite_rgb()

        if len(view_selected_files) == 1:
            if process_id == 1 or process_id == 2:
                selected_file = view_selected_files[0]

                self._view.show_image_on_canvas(
                    canvas_name="left",
                    img_or_array=selected_file,
                    image_type="rgb",
                    satellite_rgb=satellite_rgb
                )

                self._view.left_img_lf.configure(text="Source image")

                model_source_files, model_result_files = self._model_get_source_and_result_files()

                if selected_file in model_source_files:
                    index = model_source_files.index(selected_file)
                    classification = model_result_files[index][0]

                    self._view.show_image_on_canvas(
                        canvas_name="right",
                        img_or_array=classification,
                        image_type="classified",
                        satellite_rgb=satellite_rgb,
                        color_map=self._model.get_classification_color_map(classification)
                    )

                    self._view.right_img_lf.configure(text="Classified image")
                else:
                    self._view.clear_canvas("right")
            else:
                self._view.clear_canvas("left")
                self._view.clear_canvas("right")
        elif len(view_selected_files) == 2:
            if process_id == 1 or process_id == 2:
                self._view.clear_canvas("left")
                self._view.clear_canvas("right")
            elif process_id == 3:
                selected_file_1 = view_selected_files[0]
                selected_file_2 = view_selected_files[1]

                self._view.show_image_on_canvas(
                    canvas_name="left",
                    img_or_array=selected_file_1,
                    image_type="rgb",
                    satellite_rgb=satellite_rgb
                )

                self._view.left_img_lf.configure(text="Source image 1")

                self._view.show_image_on_canvas(
                    canvas_name="right",
                    img_or_array=selected_file_2,
                    image_type="rgb",
                    satellite_rgb=satellite_rgb
                )

                self._view.right_img_lf.configure(text="Source image 2")
        else:
            self._view.clear_canvas("left")
            self._view.clear_canvas("right")

    def _view_left_canvas_move_from(self, event) -> None:
        """
        Handles the start of left canvas movement event.

        :param event: event parameter
        :return: None
        """

        self._view.left_canvas.move_from(event)

    def _view_left_canvas_move_to(self, event) -> None:
        """
        Handles the end of left canvas movement event.

        :param event: event parameter
        :return: None
        """

        self._view.left_canvas.move_to(event)

    def _view_left_canvas_wheel(self, event) -> None:
        """
        Handles the zoom-in and zoom-out left canvas event.

        :param event: event parameter
        :return: None
        """

        self._view.left_canvas.wheel(event)

    def _view_right_canvas_move_from(self, event) -> None:
        """
        Handles the start of right canvas movement event.

        :param event: event parameter
        :return: None
        """

        self._view.right_canvas.move_from(event)

    def _view_right_canvas_move_to(self, event) -> None:
        """
        Handles the end of right canvas movement event.

        :param event: event parameter
        :return: None
        """

        self._view.right_canvas.move_to(event)

    def _view_right_canvas_wheel(self, event) -> None:
        """
        Handles the zoom-in and zoom-out right canvas event.

        :param event: event parameter
        :return: None
        """

        self._view.right_canvas.wheel(event)

    def _model_get_source_and_result_files(self) -> Tuple[List, List]:
        """
        Gets the source and result files from Model.

        :return: lists of source and result files
        """

        process_id = self._view.vars["process_menu"].get()

        model_source_result_files = list()

        if process_id == 1:
            model_source_result_files += self._model.result_files_hotspot
        elif process_id == 2:
            model_source_result_files += self._model.result_files_floating
        elif process_id == 3:
            model_source_result_files += self._model.result_files_washed_up

        model_source_files = list()
        model_result_files = list()

        if process_id == 1 or process_id == 2:
            model_source_files += [source_file for (source_file, classification, heatmap) in model_source_result_files]
            model_result_files += [(classification, heatmap) for (source_file, classification, heatmap) in
                                   model_source_result_files]
        elif process_id == 3:
            model_source_files += [(source_file_1, source_file_2)
                                   for (source_file_1, source_file_2, below, above) in model_source_result_files]
            model_result_files += [(below, above)
                                   for (source_file_1, source_file_2, below, above) in model_source_result_files]

        return model_source_files, model_result_files

    def _settings_working_dir_browse_directory(self) -> None:
        """
        Handles the Working Directory browse button click event in SettingsView.

        :return: None
        """

        selected_folder = fd.askdirectory(
            parent=self._view.settings_view,
            initialdir="../"
        )

        if len(selected_folder) > 0:
            self._view.settings_view.working_dir_entry.delete(0, END)
            self._view.settings_view.working_dir_entry.insert(0, selected_folder)

    def _settings_browse_file(self, button_id: str) -> None:
        """
        Handles the Random Forest path browse button click event in SettingsView.

        :param button_id: id of the clicked button
        :return: None
        """

        filetypes = (
            ("sav files", "*.sav"),
            ("All files", "*.*")
        )

        filename = fd.askopenfilename(
            parent=self._view.settings_view,
            title="Open file",
            initialdir="../",
            filetypes=filetypes,
        )

        if len(filename) > 0:
            if button_id == "hotspot":
                self._view.settings_view.hotspot_rf_entry.delete(0, END)
                self._view.settings_view.hotspot_rf_entry.insert(0, filename)
            elif button_id == "floating":
                self._view.settings_view.floating_rf_entry.delete(0, END)
                self._view.settings_view.floating_rf_entry.insert(0, filename)

    def _settings_validate_spinbox_and_entry_values(self) -> bool:
        """
        Validates all the spinbox and entry values in SettingsView.

        :return: all valid
        """

        settings_widgets = Controller._get_all_children_of_widget(self._view.settings_view)

        for widget in settings_widgets:
            if isinstance(widget, ttk.Spinbox) or isinstance(widget, ttk.Entry):
                if not widget.validate():
                    return False

        return True

    def _settings_validate_all(self) -> bool:
        """
        Validates all the input values in SettingsView.

        :return: all valid
        """

        spinbox_entry_valid = self._settings_validate_spinbox_and_entry_values()

        if not spinbox_entry_valid:
            return False

        error_message = ""

        satellite_type = self._view.settings_view.vars["satellite_rb"].get()
        blue_value = int(self._view.settings_view.sentinel_blue_spinbox.get())
        green_value = int(self._view.settings_view.sentinel_green_spinbox.get())
        red_value = int(self._view.settings_view.sentinel_red_spinbox.get())
        nir_value = int(self._view.settings_view.sentinel_nir_spinbox.get())
        heatmap_high = int(self._view.settings_view.heatmap_high_spinbox.get())
        heatmap_medium = int(self._view.settings_view.heatmap_medium_spinbox.get())
        heatmap_low = int(self._view.settings_view.heatmap_low_spinbox.get())
        garbage_mc_id = int(self._view.settings_view.garbage_mc_id_spinbox.get())
        water_mc_id = int(self._view.settings_view.water_mc_id_spinbox.get())

        bands_and_indices = ["blue", "green", "red", "nir", "pi", "ndwi", "ndvi", "rndvi", "sr"]
        values = list()
        for i in range(len(bands_and_indices)):
            index = "training_" + bands_and_indices[i]
            exec("values.append(self._view.settings_view.vars[index].get())",
                 {"values": values, "self": self, "index": index})

        if not (satellite_type in [1, 2]):
            error_message += "The Satellite type must be set!"
        elif len(np.unique([blue_value, green_value, red_value, nir_value])) != 4:
            error_message += "The Sentinel-2 settings must not contain identical values!"
        elif not (heatmap_low < heatmap_medium < heatmap_high):
            error_message += "The Heatmap probabilities must be in ascending order: low < medium < high!"
        elif garbage_mc_id == water_mc_id:
            error_message += "Garbage Class ID must not be equal to Water Class ID!"
        elif sum(values) == 0:
            error_message += "There must be at least one Training label selected!"
        else:
            for i in range(len(self._view.settings_view.color_buttons)):
                invalid = self._view.settings_view.color_buttons[i].cget("text")
                if invalid == "INVALID":
                    error_message += "There are colors incorrectly set!"
                    break

        if self._view.settings_view.state() != "normal" and len(error_message) > 0:
            return False
        elif self._view.settings_view.state() == "normal" and len(error_message) > 0:
            tkinter.messagebox.showerror("Settings value error", error_message, parent=self._view.settings_view)
            return False
        else:
            return True

    def _settings_on_ok(self) -> None:
        """
        Tries to save the user input in SettingsView, cancels in case of invalid data.

        :return: None
        """

        if not self._settings_validate_all():
            return

        # Sentinel-2 settings
        blue_value = int(self._view.settings_view.sentinel_blue_spinbox.get())
        green_value = int(self._view.settings_view.sentinel_green_spinbox.get())
        red_value = int(self._view.settings_view.sentinel_red_spinbox.get())
        nir_value = int(self._view.settings_view.sentinel_nir_spinbox.get())

        # Value settings
        n_estimators = int(self._view.settings_view.training_estimators_entry.get())
        morphology_matrix_size = int(self._view.settings_view.morphology_matrix_spinbox.get())
        morphology_iterations = int(self._view.settings_view.morphology_iterations_spinbox.get())
        washed_up_heatmap_sections = int(self._view.settings_view.washed_up_heatmap_sections_spinbox.get())
        heatmap_high = int(self._view.settings_view.heatmap_high_spinbox.get())
        heatmap_medium = int(self._view.settings_view.heatmap_medium_spinbox.get())
        heatmap_low = int(self._view.settings_view.heatmap_low_spinbox.get())
        garbage_mc_id = int(self._view.settings_view.garbage_mc_id_spinbox.get())
        water_mc_id = int(self._view.settings_view.water_mc_id_spinbox.get())

        # Path settings
        working_dir = self._view.settings_view.working_dir_entry.get()
        hotspot_rf_path = self._view.settings_view.hotspot_rf_entry.get()
        floating_rf_path = self._view.settings_view.floating_rf_entry.get()

        # File settings
        file_extension = self._view.settings_view.file_extension_entry.get()
        hotspot_classified_postfix = self._view.settings_view.hotspot_classified_postfix_entry.get()
        hotspot_heatmap_postfix = self._view.settings_view.hotspot_heatmap_postfix_entry.get()
        floating_classified_postfix = self._view.settings_view.floating_classified_postfix_entry.get()
        floating_heatmap_postfix = self._view.settings_view.floating_heatmap_postfix_entry.get()
        floating_masked_classified_postfix = self._view.settings_view.floating_masked_classified_postfix_entry.get()
        floating_masked_heatmap_postfix = self._view.settings_view.floating_masked_heatmap_postfix_entry.get()
        washed_up_before_postfix = self._view.settings_view.washed_up_before_postfix_entry.get()
        washed_up_after_postfix = self._view.settings_view.washed_up_after_postfix_entry.get()

        # Training labels
        bands_and_indices = ["blue", "green", "red", "nir", "pi", "ndwi", "ndvi", "rndvi", "sr"]
        values = list()
        for i in range(len(bands_and_indices)):
            index = "training_" + bands_and_indices[i]
            exec("values.append(self._view.settings_view.vars[index].get())",
                 {"values": values, "self": self, "index": index})

        # Satellite type
        if self._view.settings_view.vars["satellite_rb"].get() == 1:
            self._model.persistence.satellite_type = "Planet"
        elif self._view.settings_view.vars["satellite_rb"].get() == 2:
            self._model.persistence.satellite_type = "Sentinel-2"

        # Sentinel-2 settings
        self._model.persistence.sentinel_blue_band = blue_value
        self._model.persistence.sentinel_green_band = green_value
        self._model.persistence.sentinel_red_band = red_value
        self._model.persistence.sentinel_nir_band = nir_value

        # Value settings
        self._model.persistence.training_estimators = n_estimators
        self._model.persistence.morphology_matrix_size = morphology_matrix_size
        self._model.persistence.morphology_iterations = morphology_iterations
        self._model.persistence.washed_up_heatmap_sections = washed_up_heatmap_sections
        self._model.persistence.heatmap_high_prob = heatmap_high
        self._model.persistence.heatmap_medium_prob = heatmap_medium
        self._model.persistence.heatmap_low_prob = heatmap_low
        self._model.persistence.garbage_mc_id = garbage_mc_id
        self._model.persistence.water_mc_id = water_mc_id

        # Path settings
        self._model.persistence.working_dir = working_dir
        prev_hotspot_rf_path = self._model.persistence.hotspot_rf_path
        self._model.persistence.hotspot_rf_path = hotspot_rf_path
        prev_floating_rf_path = self._model.persistence.floating_rf_path
        self._model.persistence.floating_rf_path = floating_rf_path

        # File settings
        self._model.persistence.file_extension = file_extension
        self._model.persistence.hotspot_classified_postfix = hotspot_classified_postfix
        self._model.persistence.hotspot_heatmap_postfix = hotspot_heatmap_postfix
        self._model.persistence.floating_classified_postfix = floating_classified_postfix
        self._model.persistence.floating_heatmap_postfix = floating_heatmap_postfix
        self._model.persistence.floating_masked_classified_postfix = floating_masked_classified_postfix
        self._model.persistence.floating_masked_heatmap_postfix = floating_masked_heatmap_postfix
        self._model.persistence.washed_up_before_postfix = washed_up_before_postfix
        self._model.persistence.washed_up_after_postfix = washed_up_after_postfix

        # Training labels
        for i in range(len(bands_and_indices)):
            var = "self._model.persistence.training_label_" + bands_and_indices[i]
            exec("%s = %d" % (var, values[i]))

        # Color settings
        for i in range(len(self._view.settings_view.color_buttons)):
            color = self._view.settings_view.color_buttons[i].cget("bg")
            self._model.persistence.colors[i] = color

        # Save changes
        self._model.persistence.save_constants()
        try:
            self._model.load_random_forests()
        except HotspotRandomForestFileException:
            self._view.settings_view.hotspot_rf_entry.delete(0, END)
            self._view.settings_view.hotspot_rf_entry.insert(0, prev_hotspot_rf_path)
            self._model.persistence.hotspot_rf_path = prev_hotspot_rf_path
            self._model.persistence.save_constants()
            tkinter.messagebox.showerror(
                parent=self._view.settings_view,
                message="Could not load Random Forest for Hot-spot detection!\nLoading previous classifier!"
            )
            return
        except FloatingRandomForestFileException:
            self._view.settings_view.floating_rf_entry.delete(0, END)
            self._view.settings_view.floating_rf_entry.insert(0, prev_floating_rf_path)
            self._model.persistence.floating_rf_path = prev_floating_rf_path
            self._model.persistence.save_constants()
            tkinter.messagebox.showerror(
                parent=self._view.settings_view,
                message="Could not load Random Forest for Floating waste detection!\nLoading previous classifier!"
            )
            return
        except Exception:
            raise

        # Close settings window
        self._view.settings_view.hide()

        # Reload Canvas
        self._view.opened_files_lb.event_generate("<<ListboxSelect>>")

    def _settings_show(self) -> None:
        """
        Handles the displaying of SettingsView containing the previously saved data.

        :return: None
        """

        self._model.persistence.load_constants()

        # Satellite type
        if self._model.persistence.satellite_type == "Planet":
            self._view.settings_view.vars["satellite_rb"].set(1)
        elif self._model.persistence.satellite_type == "Sentinel-2":
            self._view.settings_view.vars["satellite_rb"].set(2)
        else:
            self._view.settings_view.vars["satellite_rb"].set(0)

        # Sentinel-2 settings
        blue_value = self._model.persistence.sentinel_blue_band
        self._view.settings_view.sentinel_blue_spinbox.set(blue_value)

        green_value = self._model.persistence.sentinel_green_band
        self._view.settings_view.sentinel_green_spinbox.set(green_value)

        red_value = self._model.persistence.sentinel_red_band
        self._view.settings_view.sentinel_red_spinbox.set(red_value)

        nir_value = self._model.persistence.sentinel_nir_band
        self._view.settings_view.sentinel_nir_spinbox.set(nir_value)

        # Value settings
        n_estimators = self._model.persistence.training_estimators
        self._view.settings_view.training_estimators_entry.delete(0, END)
        self._view.settings_view.training_estimators_entry.insert(0, n_estimators)

        morphology_matrix_size = self._model.persistence.morphology_matrix_size
        self._view.settings_view.morphology_matrix_spinbox.set(morphology_matrix_size)

        morphology_iterations = self._model.persistence.morphology_iterations
        self._view.settings_view.morphology_iterations_spinbox.set(morphology_iterations)

        washed_up_heatmap_sections = self._model.persistence.washed_up_heatmap_sections
        self._view.settings_view.washed_up_heatmap_sections_spinbox.set(washed_up_heatmap_sections)

        heatmap_high = self._model.persistence.heatmap_high_prob
        self._view.settings_view.heatmap_high_spinbox.set(heatmap_high)

        heatmap_medium = self._model.persistence.heatmap_medium_prob
        self._view.settings_view.heatmap_medium_spinbox.set(heatmap_medium)

        heatmap_low = self._model.persistence.heatmap_low_prob
        self._view.settings_view.heatmap_low_spinbox.set(heatmap_low)

        garbage_mc_id = self._model.persistence.garbage_mc_id
        self._view.settings_view.garbage_mc_id_spinbox.set(garbage_mc_id)

        water_mc_id = self._model.persistence.water_mc_id
        self._view.settings_view.water_mc_id_spinbox.set(water_mc_id)

        # Path settings
        working_dir = self._model.persistence.working_dir
        self._view.settings_view.working_dir_entry.delete(0, END)
        self._view.settings_view.working_dir_entry.insert(0, working_dir)

        hotspot_rf_path = self._model.persistence.hotspot_rf_path
        self._view.settings_view.hotspot_rf_entry.delete(0, END)
        self._view.settings_view.hotspot_rf_entry.insert(0, hotspot_rf_path)

        floating_rf_path = self._model.persistence.floating_rf_path
        self._view.settings_view.floating_rf_entry.delete(0, END)
        self._view.settings_view.floating_rf_entry.insert(0, floating_rf_path)

        # File settings
        file_extension = self._model.persistence.file_extension
        self._view.settings_view.file_extension_entry.delete(0, END)
        self._view.settings_view.file_extension_entry.insert(0, file_extension)

        hotspot_classified_postfix = self._model.persistence.hotspot_classified_postfix
        self._view.settings_view.hotspot_classified_postfix_entry.delete(0, END)
        self._view.settings_view.hotspot_classified_postfix_entry.insert(0, hotspot_classified_postfix)

        hotspot_heatmap_postfix = self._model.persistence.hotspot_heatmap_postfix
        self._view.settings_view.hotspot_heatmap_postfix_entry.delete(0, END)
        self._view.settings_view.hotspot_heatmap_postfix_entry.insert(0, hotspot_heatmap_postfix)

        floating_classified_postfix = self._model.persistence.floating_classified_postfix
        self._view.settings_view.floating_classified_postfix_entry.delete(0, END)
        self._view.settings_view.floating_classified_postfix_entry.insert(0, floating_classified_postfix)

        floating_heatmap_postfix = self._model.persistence.floating_heatmap_postfix
        self._view.settings_view.floating_heatmap_postfix_entry.delete(0, END)
        self._view.settings_view.floating_heatmap_postfix_entry.insert(0, floating_heatmap_postfix)

        floating_masked_classified_postfix = self._model.persistence.floating_masked_classified_postfix
        self._view.settings_view.floating_masked_classified_postfix_entry.delete(0, END)
        self._view.settings_view.floating_masked_classified_postfix_entry.insert(0, floating_masked_classified_postfix)

        floating_masked_heatmap_postfix = self._model.persistence.floating_masked_heatmap_postfix
        self._view.settings_view.floating_masked_heatmap_postfix_entry.delete(0, END)
        self._view.settings_view.floating_masked_heatmap_postfix_entry.insert(0, floating_masked_heatmap_postfix)

        washed_up_below_postfix = self._model.persistence.washed_up_before_postfix
        self._view.settings_view.washed_up_before_postfix_entry.delete(0, END)
        self._view.settings_view.washed_up_before_postfix_entry.insert(0, washed_up_below_postfix)

        washed_up_above_postfix = self._model.persistence.washed_up_after_postfix
        self._view.settings_view.washed_up_after_postfix_entry.delete(0, END)
        self._view.settings_view.washed_up_after_postfix_entry.insert(0, washed_up_above_postfix)

        # Training labels
        self._view.settings_view.vars["training_blue"].set(1 if self._model.persistence.training_label_blue else 0)
        self._view.settings_view.vars["training_green"].set(1 if self._model.persistence.training_label_green else 0)
        self._view.settings_view.vars["training_red"].set(1 if self._model.persistence.training_label_red else 0)
        self._view.settings_view.vars["training_nir"].set(1 if self._model.persistence.training_label_nir else 0)
        self._view.settings_view.vars["training_pi"].set(1 if self._model.persistence.training_label_pi else 0)
        self._view.settings_view.vars["training_ndwi"].set(1 if self._model.persistence.training_label_ndwi else 0)
        self._view.settings_view.vars["training_ndvi"].set(1 if self._model.persistence.training_label_ndvi else 0)
        self._view.settings_view.vars["training_rndvi"].set(1 if self._model.persistence.training_label_rndvi else 0)
        self._view.settings_view.vars["training_sr"].set(1 if self._model.persistence.training_label_sr else 0)

        # Color settings
        for i in range(len(self._view.settings_view.color_buttons)):
            color = self._model.persistence.colors[i]
            try:
                self._view.settings_view.color_buttons[i].configure(bg=color, activebackground=color, text="")
            except Exception:
                self._view.settings_view.color_buttons[i].configure(
                    bg="#ffffff",
                    activebackground="#ffffff",
                    fg="#000000",
                    text="INVALID"
                )

        self._view.settings_view.show()

    def _settings_color_btn_clicked(self, button: tk.Button) -> None:
        """
        Handles the color button click event in SettingsView. Changes color of button if successful.

        :param button: the clicked button
        :return: None
        """

        color = Controller._open_color_chooser_dialog(self._view.settings_view)
        if color:
            button.configure(bg=color, activebackground=color, text="")

    def _training_open_files(self) -> None:
        """
        Handles the training file opening in TrainingView.

        :return: None
        """

        new_files = self._open_files()

        if not new_files:
            return

        not_valid_band = False
        not_valid_size = False
        not_valid_extension = False

        for file in new_files:
            name, extension = os.path.splitext(file)
            if extension != ".tif":
                not_valid_extension = True
                continue
            try:
                dataset = gdal.Open(file, gdal.GA_ReadOnly)
                rows = dataset.RasterYSize
                cols = dataset.RasterXSize

                if dataset.RasterCount < 4:
                    not_valid_band = True
                    continue
                elif rows * cols > MAX_PIXEL_COUNT:
                    not_valid_size = True
                    continue

                if file not in self._model.tag_ids.keys():
                    self._model.save_training_input_file(file)
                    self._view.training_view.add_file_to_listbox(file)
            finally:
                del dataset

        if not_valid_band:
            tkinter.messagebox.showerror(
                parent=self._view.training_view.opened_files_lb,
                title="File opening",
                message="There were files with not enough bands! These were not added."
            )
        if not_valid_size:
            tkinter.messagebox.showerror(
                parent=self._view.training_view.opened_files_lb,
                title="File opening",
                message="There were too large images! The limit is " + str(MAX_PIXEL_COUNT) + " pixels. "
                                                                                              "These were not added."
            )
        if not_valid_extension:
            tkinter.messagebox.showerror(
                parent=self._view.opened_files_lb,
                title="File opening",
                message="There were images with extension other than .tif! These were not added."
            )

    def _training_delete_files(self) -> None:
        """
        Handles the training file deletion in TrainingView.

        :return: None
        """

        selected_index = self._view.training_view.opened_files_lb.curselection()

        if not selected_index:
            return

        selected_file = self._view.training_view.get_curselection_value_listbox()

        if selected_file in self._model.tag_ids.keys():
            del self._model.tag_ids[selected_file]

        if selected_file in self._model.tag_id_coords.keys():
            del self._model.tag_id_coords[selected_file]

        tag_ids = self._view.training_view.zoom_canvas.canvas.find_all()
        _ = self._model.delete_points()

        for tag_id in tag_ids:
            if self._view.training_view.zoom_canvas.is_point_or_polygon(tag_id):
                state = self._view.training_view.zoom_canvas.canvas.itemcget(tag_id, "state")
                if state == "normal":
                    self._view.training_view.zoom_canvas.delete_polygon_from_canvas([tag_id])

        self._view.training_view.remove_file_from_listbox(selected_index)

        self._view.training_view.zoom_canvas.delete_image()

        self._training_build_treeview()

    def _training_listbox_item_selected(self, event) -> None:
        """
        Handles the item selection in listbox in TrainingView.

        :param event: event parameter
        :return: None
        """

        selected_file = self._view.training_view.get_curselection_value_listbox()

        if selected_file is None:
            return

        tag_ids = self._view.training_view.zoom_canvas.canvas.find_all()

        _ = self._model.delete_points()

        for tag_id in tag_ids:
            if self._view.training_view.zoom_canvas.is_point_or_polygon(tag_id):
                state = self._view.training_view.zoom_canvas.canvas.itemcget(tag_id, "state")
                if state == "normal":
                    self._view.training_view.zoom_canvas.hide_shape(tag_id)

        satellite_rgb = self._get_satellite_rgb()

        self._view.training_view.zoom_canvas.open_image(selected_file, "rgb", satellite_rgb)

        for mc_id in self._model.tag_ids[selected_file].keys():
            for tag_id in self._model.tag_ids[selected_file][mc_id][2]:
                self._view.training_view.zoom_canvas.show_shape(tag_id)

        self._training_build_treeview()

    def _training_add_new(self) -> None:
        """
        Handles the addition of new Class in TrainingView.

        :return: None
        """

        selected_file = self._view.training_view.get_curselection_value_listbox()

        if selected_file is None:
            return

        mc_id = self._view.training_view.get_mc_id()
        mc_name = self._view.training_view.get_mc_name()
        mc_color = self._view.training_view.get_mc_color()
        mc_ids = list(self._model.tag_ids[selected_file].keys())
        mc_names = [value[0].lower() for value in self._model.tag_ids[selected_file].values()]

        if len(mc_name) == 0:
            message = "Invalid MC Name!"
            tkinter.messagebox.showerror(parent=self._view.training_view, title="Error", message=message)
            return

        if (mc_id in mc_ids) or (mc_name in mc_names):
            message = "MC ID or MC Name already in use!"
            tkinter.messagebox.showerror(parent=self._view.training_view, title="Error", message=message)
            return

        self._model.save_new_mc(selected_file, mc_id, mc_name, mc_color)

        self._training_build_treeview()

    def _training_delete(self) -> None:
        """
        Handles the deletion of a Class in TrainingView.

        :return: None
        """

        selected_file = self._view.training_view.get_curselection_value_listbox()
        selection = self._view.training_view.get_selection_treeview()

        if (selected_file is None) or (len(selection) == 0):
            return

        selected_item = self._view.training_view.treeview.item(selection[0])
        mc_id = selected_item["values"][1]

        if len(str(mc_id)) == 0:
            tag_id = int(selected_item["values"][2])
            self._model.delete_tag_id(selected_file, tag_id)
            self._view.training_view.zoom_canvas.delete_polygon_from_canvas([tag_id])
        else:
            tag_ids = self._model.delete_mc(selected_file, int(mc_id))
            self._view.training_view.zoom_canvas.delete_polygon_from_canvas(tag_ids)

        self._training_build_treeview()

    def _training_disable_treeview_column_resizing(self, event) -> str:
        """
        Disables the resizing of columns in TrainingView treeview.

        :param event: event parameter
        :return: "break" string to cancel resizing
        """

        if self._view.training_view.treeview.identify_region(event.x, event.y) != "cell":
            return "break"

    def _training_treeview_item_selected(self, event) -> None:
        """
        Handles the item selection in treeview in TrainingView.

        :param event: event parameter
        :return: None
        """

        selected_file = self._view.training_view.get_curselection_value_listbox()
        selection = self._view.training_view.get_selection_treeview()[0]
        selected_item = self._view.training_view.treeview.item(selection)

        mc_name = selected_item["values"][0]
        mc_id = selected_item["values"][1]

        if len(mc_name) == 0:
            return

        mc_color = self._model.tag_ids[selected_file][mc_id][1]

        self._view.training_view.set_mc_id(int(mc_id))
        self._view.training_view.set_mc_name(mc_name)
        self._view.training_view.set_color_btn_bg(mc_color)

    def _training_change_color_btn_color(self) -> None:
        """
        Handles the color change of color button in TrainingView.

        :return: None
        """

        color = Controller._open_color_chooser_dialog(self._view.training_view)
        if color:
            self._view.training_view.set_color_btn_bg(color)

    def _training_start_on_separate_thread(self) -> None:
        """
        Start the training process on a separate thread.

        :return: None
        """

        if not self._settings_validate_all():
            tkinter.messagebox.showerror("Settings error", "There are values wrongly set in Settings!",
                                         parent=self._view)
            return

        process_thread = threading.Thread(target=self._training_start, daemon=True)
        process_thread.start()

    def _training_start(self) -> None:
        """
        Handles the training process in TrainingView.

        :return: None
        """

        selected_index = self._view.training_view.opened_files_lb.curselection()
        try:
            self._view.training_view.process_pb.configure(mode="indeterminate")
            self._view.training_view.process_pb.start(25)
            Controller._disable_all_children(self._view)
            self._view.training_view.opened_files_lb.configure(state="normal")
            self._view.training_view.opened_files_lb.unbind("<<ListboxSelect>>")
            self._view.training_view.update()

            self._training_save_coords_of_tag_ids()

            usable_data, enough_data = self._model.create_usable_training_data()

            if not enough_data:
                self._view.training_view.zoom_canvas.delete_image()
                self._view.training_view.opened_files_lb.selection_clear(0, END)

                message = "Not enough training data!"
                tkinter.messagebox.showerror(title="Training error", message=message, parent=self._view.training_view)

                return

            df = self._model.create_training_df(usable_data)
            df.sort_values(by=["FID", "COD"], inplace=True)

            file = self._save_file("sav")
            if file:
                name, extension = os.path.splitext(file.name)
                file.close()
                df.to_csv(name + ".csv", sep=";", index=False)
                self._model.create_and_save_random_forest(name + ".csv", name + extension)

                tkinter.messagebox.showinfo(
                    parent=self._view.training_view.zoom_canvas,
                    title="Training info",
                    message="Training is complete!\nGo to Settings to reconfigure application!"
                )
            else:
                tkinter.messagebox.showerror(
                    parent=self._view.training_view.zoom_canvas,
                    title="Error",
                    message="Training interrupted!"
                )
        except Exception as exc:
            message = traceback.format_exception_only(type(exc), exc)[0]
            if len(message) == 0:
                message = traceback.format_exc()
            tkinter.messagebox.showerror(
                title="Error",
                message=message
            )
        finally:
            self._enable_all_children(self._view)
            self._view.training_view.opened_files_lb.bind("<<ListboxSelect>>", self._training_listbox_item_selected)
            self._view.training_view.opened_files_lb.selection_clear(0, END)
            if selected_index:
                self._view.training_view.opened_files_lb.selection_set(selected_index)
            self._view.training_view.opened_files_lb.event_generate("<<ListboxSelect>>")
            self._view.training_view.process_pb.stop()
            self._view.training_view.process_pb.configure(value=0, mode="determinate")

    def _training_place_point_on_canvas(self, event) -> None:
        """
        Handles point placement on canvas in TrainingView.

        :param event: event parameter
        :return: None
        """

        tag_id = self._view.training_view.zoom_canvas.place_point_on_canvas(event)
        if not (tag_id is None):
            self._model.save_point_on_canvas(tag_id)

    def _training_place_polygon_on_canvas(self, event) -> None:
        """
        Handles polygon placement on canvas in TrainingView.

        :param event: event parameter
        :return: None
        """

        selected_training_file = self._view.training_view.get_curselection_value_listbox()
        selected_mc = self._view.training_view.get_selection_treeview()

        if (selected_training_file is None) or (len(selected_mc) == 0):
            return

        selected_mc_item = self._view.training_view.treeview.item(selected_mc[0])
        mc_id = str(selected_mc_item["values"][1])

        if len(mc_id) == 0:
            return

        tag_ids = self._model.place_polygon_on_canvas()
        coords = self._view.training_view.get_coords_of_points_on_canvas(tag_ids)

        if coords:
            mc_id, mc_name, color, tag_id = self._view.training_view.place_polygon_on_canvas(coords)
            self._model.save_tag_id(selected_training_file, mc_id, mc_name, color, tag_id)
            self._training_build_treeview()
            self._view.training_view.zoom_canvas.delete_points_from_canvas(tag_ids)

    def _training_canvas_move_from(self, event) -> None:
        """
        Handles the start of movement of canvas in TrainingView.

        :param event: event parameter
        :return: None
        """

        self._view.training_view.zoom_canvas.move_from(event)

    def _training_canvas_move_to(self, event) -> None:
        """
        Handles the end of movement of canvas in TrainingView.

        :param event: event parameter
        :return: None
        """

        self._view.training_view.zoom_canvas.move_to(event)

    def _training_canvas_wheel(self, event) -> None:
        """
        Handles the zoom-in zoom-out of canvas in TrainingView.

        :param event: event parameter
        :return: None
        """

        self._view.training_view.zoom_canvas.wheel(event)

    def _training_load_csv(self) -> None:
        """
        Handles training data loading
        :return: None
        """
        csvFileName = self._open_files()[0]

        if csvFileName:
            name, extension = os.path.splitext(csvFileName)
            self._model.create_and_save_random_forest(name + extension, name + '.sav')

            tkinter.messagebox.showinfo(
                parent=self._view.training_view.zoom_canvas,
                title="Training info",
                message="Training is complete!\nGo to Settings to reconfigure application!"
            )    


    def _training_on_closing(self) -> None:
        """
        Handles the TrainingView closing event.

        :return: None
        """

        self._view.training_view.withdraw()
        self._view.update()
        self._view.deiconify()

    def _training_build_treeview(self) -> None:
        """
        Rebuilds the treeview in TrainingView.

        :return: None
        """

        self._view.training_view.clear_treeview()
        selected_file = self._view.training_view.get_curselection_value_listbox()

        if selected_file is None:
            return

        tag_ids = self._model.tag_ids
        for mc_id in tag_ids[selected_file].keys():
            mc_name, color, tags = tag_ids[selected_file][mc_id]
            self._view.training_view.insert_into_treeview(parent="", index=mc_id, iid=mc_id,
                                                          values=(mc_name, mc_id, ""))
            for tag in tags:
                self._view.training_view.insert_into_treeview(parent=str(mc_id), index=tag, iid=None,
                                                              values=("", "", tag))

    def _training_save_coords_of_tag_ids(self) -> None:
        """
        Start the save process of training data.

        :return: None
        """

        self._view.training_view.rescale_to_original_size()
        tag_ids = self._model.tag_ids

        for i in range(self._view.training_view.opened_files_lb.size()):
            self._view.training_view.opened_files_lb.bind("<<ListboxSelect>>", self._training_listbox_item_selected)
            self._view.training_view.opened_files_lb.selection_clear(0, END)
            self._view.training_view.opened_files_lb.selection_set(i)
            self._view.training_view.opened_files_lb.event_generate("<<ListboxSelect>>")
            selected_file = self._view.training_view.get_curselection_value_listbox()
            self._view.training_view.opened_files_lb.unbind("<<ListboxSelect>>")
            for mc_id in tag_ids[selected_file].keys():
                mc_name, color, tags = tag_ids[selected_file][mc_id]
                coords, bbox_coords = self._view.training_view.get_coords_of_tag_id_on_canvas(tags)
                self._model.save_tag_id_coords(selected_file, mc_id, mc_name, coords, bbox_coords)

    def _get_satellite_rgb(self) -> List[int]:
        """
        Gets the saved RGB band indices based on the selected satellite type.

        :return: list of indices
        """

        satellite_rgb = list()
        if self._model.persistence.satellite_type == "Planet":
            red = self._model.persistence.planet_red_band
            green = self._model.persistence.planet_green_band
            blue = self._model.persistence.planet_blue_band
            satellite_rgb += [red, green, blue]
        elif self._model.persistence.satellite_type == "Sentinel-2":
            red = self._model.persistence.sentinel_red_band
            green = self._model.persistence.sentinel_green_band
            blue = self._model.persistence.sentinel_blue_band
            satellite_rgb += [red, green, blue]
        return satellite_rgb

    def _show_about(self) -> None:
        """
        Displays a Messagebox with the content of "about.txt"

        :return: None
        """

        with open("about.txt", mode="r") as file:
            text = file.read()
            tkinter.messagebox.showinfo(
                parent=self._view,
                title="About",
                message=text
            )

    def _open_files(self) -> List[str]:
        """
        Handles the file opening with an Open File Dialog.

        :return: list of opened file paths
        """

        active_window = self._view.get_active_window()

        filetypes = (
            ("tif files", "*.tif"),
            ("All files", "*.*")
        )

        filenames = fd.askopenfilenames(
            parent=active_window,
            title="Open files",
            initialdir="../",
            filetypes=filetypes,
        )

        return list(filenames)

    def _save_file(self, file_extension: str) -> Union[TextIO, None]:
        """
        Opens File Save Dialog.

        :param file_extension: extension of file to be saved
        :return: TextIO if successful
        """

        active_window = self._view.get_active_window()

        filetypes = None

        if file_extension == "geojson":
            filetypes = (
                ("GeoJSON file", "*.geojson"),
                ("All files", "*.*")
            )
        elif file_extension == "sav":
            filetypes = (
                ("SAV file", "*.sav"),
                ("All files", "*.*")
            )
        else:
            return None

        file = fd.asksaveasfile(
            parent=active_window,
            title="Save file",
            initialdir="../",
            initialfile="Untitled." + file_extension,
            defaultextension="." + file_extension,
            filetypes=filetypes
        )

        return file

    def _enable_all_children(self, widget) -> None:
        """
        Enables all the given widget's children.

        :param widget: the given widget
        :return: None
        """

        children = Controller._get_all_children_of_widget(widget)

        for child in children:
            try:
                child.configure(state="normal")
            except tk.TclError:
                continue

        self._view_update_start_process_btn_state()

        widget.update()

    # Methods for invalid input handling in SettingsView
    def _invalid_sentinel_band(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Values in the Sentinel-2 settings must be numbers between 1 and 13!"
            tkinter.messagebox.showerror("Sentinel-2 settings value error", message, parent=self._view.settings_view)

    def _invalid_decision_tree_number(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Number of decision trees must be between 1 and 1000!"
            tkinter.messagebox.showerror("Number of decision trees value error", message,
                                         parent=self._view.settings_view)

    def _invalid_morphology(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Matrix size for morphology must be a number between 1 and 20!"
            tkinter.messagebox.showerror("Matrix size for morphology value error", message,
                                         parent=self._view.settings_view)

    def _invalid_iterations(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Number of iterations for morphology must be between 1 and 20!"
            tkinter.messagebox.showerror("Number of iterations for morphology value error", message,
                                         parent=self._view.settings_view)

    def _invalid_heatmap_sections(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Washed up waste pixel uniqueness modifier must be a number between 4 and 20!"
            tkinter.messagebox.showerror("Washed up waste pixel uniqueness modifier value error", message,
                                         parent=self._view.settings_view)

    def _invalid_heatmap(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Heatmap probabilities must be numbers between 1 and 100!"
            tkinter.messagebox.showerror("Heatmap probabilities value error", message, parent=self._view.settings_view)

    def _invalid_settings_mc_id(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Garbage Class ID and Water Class ID must be a number between 1 and 15!"
            tkinter.messagebox.showerror("Garbage Class ID and Water Class ID value error", message,
                                         parent=self._view.settings_view)

    def _invalid_working_dir(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Working directory does not exist!"
            tkinter.messagebox.showerror("Working directory path error", message, parent=self._view.settings_view)

    def _invalid_file_path(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Random Forest file does not exist!"
            tkinter.messagebox.showerror("Random Forest file path error", message, parent=self._view.settings_view)

    def _invalid_file_extension(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Incorrect file extension! It must not contain the following characters: < > : \" / \\ | ? * ."
            tkinter.messagebox.showerror("File extension value error", message, parent=self._view.settings_view)

    def _invalid_postfix(self) -> None:
        if self._view.settings_view.state() == "normal":
            message = "Incorrect postfix! It must not contain the following characters: < > : \" / \\ | ? *"
            tkinter.messagebox.showerror("File postfix value error", message, parent=self._view.settings_view)

    # Static protected methods
    @staticmethod
    def _get_all_children_of_widget_r(widget, set_children: Set) -> None:
        """
        Recursively gets all the children of widget.

        :param widget: the given widget
        :param set_children: set of children
        :return: None
        """

        set_children.add(widget)
        if widget.winfo_children():
            for child in widget.winfo_children():
                set_children.add(child)
                Controller._get_all_children_of_widget_r(child, set_children)

    @staticmethod
    def _get_all_children_of_widget(widget) -> Set:
        """
        Calls the function that recursively gets all the children of widget.

        :param widget: the given widget
        :return: set of children
        """

        set_children = set()
        Controller._get_all_children_of_widget_r(widget, set_children)
        return set_children

    @staticmethod
    def _disable_all_children(widget) -> None:
        """
        Disables all the given widget's children.

        :param widget: the given widget
        :return: None
        """

        children = Controller._get_all_children_of_widget(widget)

        for child in children:
            try:
                child.configure(state="disabled")
            except tk.TclError:
                continue

        widget.update()

    @staticmethod
    def _open_color_chooser_dialog(window: ttk.Toplevel) -> Union[str, None]:
        """
        Opens a ColorChooserDialog to select a new color.

        :param window: dialog to be placed on top of this window
        :return: None
        """

        try:
            cd = ColorChooserDialog(window)
            cd.show()
            color = cd.result

            if color:
                return color.hex

            return None
        except Exception:
            return None

    # Methods for validating user input in SettingsView
    @staticmethod
    def _validate_sentinel_band(x: str) -> bool:
        """
        Validates sentinel band number in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        return x.isdigit() and 1 <= int(x) <= 13

    @staticmethod
    def _validate_decision_tree_number(x: str) -> bool:
        """
        Validates decision tree number in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        return x.isdigit() and 1 <= int(x) <= 1000

    @staticmethod
    def _validate_morphology(x: str) -> bool:
        """
        Validates morphology matrix size and iteration count in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        return x.isdigit() and 1 <= int(x) <= 20

    @staticmethod
    def _validate_heatmap(x: str) -> bool:
        """
        Validates heatmap probability value in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        return x.isdigit() and 1 <= int(x) <= 100

    @staticmethod
    def _validate_settings_mc_id(x: str) -> bool:
        """
        Validates Garbage and Water Class ID in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        return x.isdigit() and 1 <= int(x) <= 15

    @staticmethod
    def _validate_training_mc_id(x: str) -> bool:
        """
        Validates Garbage and Water Class ID in TrainingView.

        :param x: entry input
        :return: valid or not
        """

        return x.isdigit() and 1 <= int(x) <= 15

    @staticmethod
    def _validate_heatmap_sections(x: str) -> bool:
        """
        Validates uniqueness modifier in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        return x.isdigit() and 1 <= int(x) <= 20

    @staticmethod
    def _validate_working_dir(x: str) -> bool:
        """
        Validates working directory path in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        if x == "":
            return False
        elif os.path.exists(x + "/"):
            return True
        else:
            return False

    @staticmethod
    def _validate_file_path(x: str) -> bool:
        """
        Validates file path in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        if os.path.exists(x):
            return True
        else:
            return False

    @staticmethod
    def _validate_file_extension(x: str) -> bool:
        """
        Validates file extension in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        not_allowed = list('<>:"/\|?*.')
        any([letter for letter in list(x)])
        return not (any([letter in not_allowed for letter in list(x)]))

    @staticmethod
    def _validate_postfix(x: str) -> bool:
        """
        Validates file name postfix in SettingsView.

        :param x: entry input
        :return: valid or not
        """

        not_allowed = list('<>:"/\|?*')
        any([letter for letter in list(x)])
        return (x == "") or not (any([letter in not_allowed for letter in list(x)]))

    @staticmethod
    def _validate_alpha(x) -> bool:
        """
        Validates the MC NAME entry value in TrainingView.

        :param x: entry input
        :return: valid or not
        """

        if x.isdigit() or len(x) > 12:
            return False
        else:
            return True
