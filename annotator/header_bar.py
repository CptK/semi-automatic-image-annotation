"""Header bar module for the annotator application."""

import os
from tkinter import DoubleVar, StringVar, filedialog

import customtkinter as ctk

from annotator.classes_popup import ClassesPopup
from annotator.controller import Controller


class ExportPopup(ctk.CTkToplevel):
    """Export popup window for the annotator application.

    Args:
        master: The parent widget.
        export_func: The export function to call with the export options.
    """

    def __init__(self, master, export_func, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Export Options")
        self.geometry("400x400")
        self.export_func = export_func
        self.export_formats = ["CSV", "JSON", "YOLO"]

        # Warning message
        self.warn_msg = ctk.CTkLabel(self, text="", text_color="red")
        self.warn_msg.pack(pady=(10, 0))

        # Path selection frame
        self.path_frame = ctk.CTkFrame(self, bg_color="transparent")
        self.path_frame.pack(pady=(20, 10), padx=20, fill="x")

        self.path_label = ctk.CTkLabel(self.path_frame, text="Export Path:")
        self.path_label.pack(side="left", padx=(0, 10))

        self.path_entry = ctk.CTkEntry(self.path_frame, width=200)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_button = ctk.CTkButton(self.path_frame, text="Browse", command=self._browse_path)
        self.browse_button.pack(side="left")

        # Export format frame
        self.format_frame = ctk.CTkFrame(self)
        self.format_frame.pack(pady=(10, 20), padx=20, fill="x")

        self.format_label = ctk.CTkLabel(self.format_frame, text="Export Format:")
        self.format_label.pack(side="left", padx=(0, 10))

        self.format_var = StringVar(value="Select format")
        self.format_combobox = ctk.CTkComboBox(
            self.format_frame,
            variable=self.format_var,
            values=self.export_formats,
            command=self._on_format_selected,
        )
        self.format_combobox.pack(side="left", fill="x", expand=True)

        # Checkboxes
        self.checkbox_var1 = ctk.BooleanVar()
        self.checkbox1 = ctk.CTkCheckBox(
            self, text="Only export images marked as ready", variable=self.checkbox_var1
        )
        self.checkbox1.pack(pady=(10, 0))

        # Train-test split frame
        self.split_frame = ctk.CTkFrame(self)
        self.split_frame.pack(pady=(10, 10), padx=20, fill="x")

        self.split_label = ctk.CTkLabel(self.split_frame, text="Train Split:")
        self.split_label.pack(side="left", padx=(0, 10))

        self.split_value = DoubleVar(value=0.8)  # Initialize with a default value
        self.split_value_label = ctk.CTkLabel(self.split_frame, textvariable=self.split_value)
        self.split_value_label.pack(side="right", padx=(10, 0))

        self.slider = ctk.CTkSlider(
            self.split_frame,
            from_=0,
            to=1,
            width=200,
            variable=self.split_value,
            command=self._update_split_value,
        )
        self.slider.pack(side="left", fill="x", expand=True)

        # remove the split frame for now because YOLO is not the default format
        self.split_frame.pack_forget()

        # Export button
        self.export_button = ctk.CTkButton(self, text="Export", command=self._export_data)
        self.export_button.pack(pady=20)

    def _browse_path(self):
        """Browse for the export path."""
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, ctk.END)
            self.path_entry.insert(0, path)

    def _export_data(self):
        """Export the data using the selected options."""
        export_path = self.path_entry.get()
        export_format = self.format_var.get()
        option1 = self.checkbox_var1.get()
        option2 = self.slider.get()

        if export_format not in self.export_formats:
            self.warn_msg.configure(text="Please select a valid export format.")
            return

        if export_path == "":
            # get the current path
            export_path = os.getcwd()

            if export_format == "YOLO":
                export_path = os.path.join(export_path, "yolo_export")

        try:
            self.export_func(export_path, export_format, option1, option2)
            self.destroy()
        except Exception as e:
            self.warn_msg.configure(text=str(e))
            raise e

    def _update_split_value(self, value):
        """Update the train split value label."""
        self.split_value.set(round(float(value), 2))

    def _on_format_selected(self, event):
        """Show the train-test split frame if YOLO format is selected."""
        if self.format_var.get() == "YOLO":
            self.split_frame.pack(pady=(10, 10), padx=20, fill="x", before=self.export_button)
        else:
            self.split_frame.pack_forget()


class HeaderBar(ctk.CTkFrame):
    """Header bar for the annotator application.

    Args:
        master: The parent widget.
        export_func: The export function to call with the export options.
    """

    def __init__(self, master, controller: Controller, **kwargs):
        super().__init__(master, **kwargs)

        self.export_button = ctk.CTkButton(self, text="Export", command=self._export)
        self.export_button.pack(side="left", padx=10)
        self.controller = controller

        self.classes_button = ctk.CTkButton(self, text="Classes", command=self._show_classes_popup)
        self.classes_button.pack(side="left", padx=10)

        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self,
            values=["Light", "Dark", "System"],
            command=self._change_appearance_mode_event,
            variable=StringVar(value="System"),
        )
        self.appearance_mode_optionemenu.pack(side="right", padx=10)

    def _export(self):
        """Show the export popup window."""
        popup = ExportPopup(self.master, self.controller.export)
        popup.grab_set()

    def _show_classes_popup(self):
        """Show the classes popup window."""
        popup = ClassesPopup(self.master, self.controller)
        popup.grab_set()

    def _change_appearance_mode_event(self, new_appearance_mode: str):
        """Change the appearance mode of the application."""
        ctk.set_appearance_mode(new_appearance_mode)
