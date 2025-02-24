from collections.abc import Callable
from tkinter import IntVar, StringVar, filedialog

import customtkinter as ctk

from annotator.classes_popup import ClassItem
from annotator.controller import Controller


class ClassesContainer(ctk.CTkScrollableFrame):
    """Container for the class items.

    Contains a label for displaying a warning message, a list of class items, and buttons to add and delete
    classes.

    Args:
        master: The parent widget.
        controller: The controller object.
        can_delete: The function to check if a class can be deleted.
    """

    def __init__(self, master, controller: Controller, can_delete: Callable, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.class_items: list[ClassItem] = []
        self.controller = controller
        self.can_delete = can_delete

        self.default_class_uid = IntVar(value=self.controller.get_default_class_uid())
        self.default_class_uid.trace_add("write", self.update_default_uid)

        for cls in self.controller.class_iter():
            self.add_class_item(cls["name"], cls["color"], cls["uid"])

    def add_class_item(self, class_name: str, class_color: str, uid: int) -> None:
        """Add a class item to the container.

        Args:
            class_name: The name of the class.
            class_color: The color of the class.
            uid: The unique identifier of the class.
        """
        class_item = ClassItem(
            self,
            self.controller,
            class_name,
            class_color,
            self.default_class_uid,
            uid,
            self.delete_class_item,
            fg_color=self.cget("fg_color"),
        )
        class_item.pack(fill="x", pady=(0, 5))
        self.class_items.append(class_item)

    def delete_class_item(self, del_item: ClassItem) -> None:
        """Delete a class item from the container.

        Opens a popup window to confirm the deletion. Only deletes the class item if the user confirms the
        deletion. This method also removes the class item from the container, the actual deletion is done in
        the popup window.

        Args:
            del_item: The class item to delete.
        """
        if not self.can_delete(del_item.uid):
            return
        self.controller.delete_class(del_item.uid, redraw=False)
        if del_item.uid not in self.controller.available_class_uids():
            del_item.pack_forget()
            self.class_items.remove(del_item)

    def update_default_uid(self, *args) -> None:
        """Update the default class UID in the controller."""
        self.controller.set_default_class_uid(self.default_class_uid.get())


class NewProjectWindow(ctk.CTkToplevel):
    """Window for creating a new project.

    Allows users to:
    - Set project name and location
    - Set up initial classes
    """

    def __init__(self, master, controller: Controller, on_create: Callable, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title("New Project")
        self.geometry("600x700")
        self.resizable(False, False)

        self.controller = controller
        self.on_create = on_create

        # Project settings variables
        self.project_name = StringVar(value="")
        self.project_description = StringVar(value="")
        self.project_path = StringVar(value="")

        self.setup_ui()

        # Make the window modal
        self.grab_set()
        self.transient(master)
        self.focus_set()

    def setup_ui(self) -> None:
        """Set up the user interface components."""
        # Main container
        self.container = ctk.CTkFrame(self, fg_color=self.cget("fg_color"))
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Project Settings Section
        self.setup_project_settings()

        # Classes Section
        self.setup_classes_section()

        # Warning Label
        self.warning_label = ctk.CTkLabel(self.container, text="", text_color="red")
        self.warning_label.pack(pady=(0, 10))

        # Buttons
        self.setup_buttons()

    def setup_project_settings(self) -> None:
        """Set up the project settings section."""
        # Project Settings Frame
        settings_frame = ctk.CTkFrame(self.container)
        settings_frame.pack(fill="x", pady=(0, 20))

        # Title
        title_label = ctk.CTkLabel(settings_frame, text="Project Settings", font=("Arial Bold", 16))
        title_label.pack(anchor="w", pady=(10, 20), padx=10)

        # Project Name
        name_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        name_frame.pack(fill="x", padx=10, pady=(0, 10))

        name_label = ctk.CTkLabel(name_frame, text="Project Name:")
        name_label.pack(side="left")

        name_entry = ctk.CTkEntry(name_frame, textvariable=self.project_name)
        name_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Project Description
        description_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        description_frame.pack(fill="x", padx=10, pady=(0, 10))

        description_label = ctk.CTkLabel(description_frame, text="Description:")
        description_label.pack(side="left")

        description_entry = ctk.CTkEntry(description_frame, textvariable=self.project_description)
        description_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Project Path
        path_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=(0, 10))

        path_label = ctk.CTkLabel(path_frame, text="Location:")
        path_label.pack(side="left")

        path_entry = ctk.CTkEntry(path_frame, textvariable=self.project_path)
        path_entry.pack(side="left", fill="x", expand=True, padx=(10, 10))

        browse_button = ctk.CTkButton(path_frame, text="Browse", command=self.browse_path, width=100)
        browse_button.pack(side="right")

    def setup_classes_section(self) -> None:
        """Set up the classes section."""
        # Classes Frame
        classes_frame = ctk.CTkFrame(self.container)
        classes_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Title
        title_label = ctk.CTkLabel(classes_frame, text="Classes", font=("Arial Bold", 16))
        title_label.pack(anchor="w", pady=(10, 20), padx=10)

        # Classes Container
        self.classes_container = ClassesContainer(
            classes_frame, self.controller, self.can_delete_class, fg_color=classes_frame.cget("fg_color")
        )
        self.classes_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Add Class Button
        add_class_button = ctk.CTkButton(classes_frame, text="Add Class", command=self.add_class)
        add_class_button.pack(anchor="w", padx=10, pady=(0, 10))

    def setup_buttons(self) -> None:
        """Set up the bottom buttons."""
        button_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 10))

        cancel_button = ctk.CTkButton(
            button_frame, text="Cancel", command=self.destroy, fg_color="transparent", border_width=1
        )
        cancel_button.pack(side="left", padx=(0, 10))

        create_button = ctk.CTkButton(button_frame, text="Create Project", command=self.create_project)
        create_button.pack(side="right")

    def browse_path(self) -> None:
        """Open a directory browser dialog."""
        path = filedialog.askdirectory()
        if path:
            self.project_path.set(path)

    def add_class(self) -> None:
        """Add a new class to the container."""
        new_class = self.controller.add_new_init_class()
        self.classes_container.add_class_item(new_class["name"], new_class["color"], new_class["uid"])

    def can_delete_class(self, uid: int) -> bool:
        """Check if a class can be deleted."""
        if self.controller.get_number_classes() == 1:
            self.warning_label.configure(text="Cannot delete the last class.")
            return False
        if self.controller.get_default_class_uid() == uid:
            self.warning_label.configure(text="Cannot delete the default class.")
            return False
        return True

    def validate_inputs(self) -> bool:
        """Validate all inputs before creating the project."""
        if not self.project_name.get().strip():
            self.warning_label.configure(text="Project name is required.")
            return False

        if not self.project_path.get().strip():
            self.warning_label.configure(text="Project location is required.")
            return False

        # Validate class names
        class_names = [item.class_name.get() for item in self.classes_container.class_items]
        if len(class_names) != len(set(class_names)):
            self.warning_label.configure(text="Cannot have two classes with the same name.")
            return False

        return True

    def create_project(self) -> None:
        """Create the project with the specified settings.

        Collects all the project settings and class information, validates them,
        and calls the creation callback with the project data if everything is valid."""
        if not self.validate_inputs():
            return

        class_names = [item.class_name.get() for item in self.classes_container.class_items]
        uids = [item.uid for item in self.classes_container.class_items]
        self.controller.change_class_name(uids, class_names)

        # Create project data
        project_data = {
            "project_name": self.project_name.get(),
            "project_path": self.project_path.get(),
            "class_store": self.controller.classes_store(),
            "image_store": self.controller.image_store(),
            "default_class_uid": self.classes_container.default_class_uid.get(),
            "description": self.project_description.get(),
        }

        # Call the creation callback
        self.on_create(project_data, self.controller)

        # Close the window
        self.destroy()
