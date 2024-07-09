"""Module for the popup window that allows the user to manage classes."""

from collections.abc import Callable
from tkinter import IntVar, StringVar, colorchooser

import customtkinter as ctk

from annotator.controller import Controller


class ClassDeletionPopup(ctk.CTkToplevel):
    """Popup window for deleting a class.

    The user can choose to either delete all bounding boxes with the class or change the class of the bounding
    boxes.

    Args:
        master: The parent widget.
        controller: The controller object.
        uid: The UID of the class to delete.
    """

    def __init__(self, master, controller: Controller, uid: int, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title("Delete Class")
        self.resizable(False, False)
        self.controller = controller
        self.uid = uid

        self.radio_var = IntVar(value=1)
        self.new_class_var = StringVar()

        # Create description
        label = self.controller.get_class_name(self.uid)
        texts = [
            f"Are you sure you want to delete the class '{label}'?",
            "This action cannot be undone.",
            f"\nWhat would you like to do with the bounding boxes having the class '{label}'?",
        ]
        text = " ".join(texts)
        self.description = ctk.CTkLabel(self, text=text, wraplength=300, justify="left")
        self.description.pack(side="top", pady=(20, 10), padx=10, expand=True, fill="x")

        # Create radio buttons
        self.radio_delete = ctk.CTkRadioButton(
            self,
            text="Delete all bounding boxes with the\nrespective class",
            variable=self.radio_var,
            value=1,
            command=self.hide_class_options,
        )
        self.radio_delete.pack(padx=15, pady=10, expand=True, fill="x")

        self.radio_rename = ctk.CTkRadioButton(
            self,
            text="Give all boxes with the old class a\nnew class",
            variable=self.radio_var,
            value=2,
            command=self.show_class_options,
        )
        self.radio_rename.pack(padx=15, pady=10, expand=True, fill="x")

        # Placeholder for the class options
        self.class_options_frame = ctk.CTkFrame(self, height=30, fg_color=self.cget("fg_color"))
        self.class_options_frame.pack(pady=10, padx=15, expand=True, fill="x")

        class_options = self.controller.available_labels()
        class_options.remove(self.controller.get_class_name(self.uid))
        self.class_options_label = ctk.CTkLabel(self.class_options_frame, text="Select a new class:")
        self.class_options_menu = ctk.CTkOptionMenu(
            self.class_options_frame, variable=self.new_class_var, values=class_options
        )
        self.class_options_label.pack_forget()
        self.class_options_menu.pack_forget()

        # Create buttons
        self.cancel_button = ctk.CTkButton(self, text="Cancel", command=self.cancel)
        self.cancel_button.pack(side="left", padx=15, pady=20)

        self.submit_button = ctk.CTkButton(self, text="Submit", command=self.submit)
        self.submit_button.pack(side="right", padx=15, pady=20)

        # Make the popup modal
        self.grab_set()
        self.transient(master)
        self.focus_set()

    def show_class_options(self) -> None:
        """Show the class options when the second radio button is selected."""
        self.class_options_label.pack(side="left")
        self.class_options_menu.pack(side="right")

    def hide_class_options(self) -> None:
        """Hide the class options when the first radio button is selected."""
        self.class_options_label.pack_forget()
        self.class_options_menu.pack_forget()

    def cancel(self) -> None:
        """Cancel the deletion."""
        self.grab_release()
        self.destroy()

    def submit(self) -> None:
        """Submit the deletion.

        The action depends on the selected radio button. If the first radio button is selected, all bounding
        boxes with the class are deleted. If the second radio button is selected, the class of the bounding
        boxes is changed to the selected class.
        """
        action = self.radio_var.get()
        if action == 1:
            self.controller.delete_class(uid=self.uid, change_classes_uid=None, redraw=True)
        elif action == 2:
            new_class = self.new_class_var.get()
            if not new_class:
                return
            new_uid = self.controller.get_class_uid(new_class)
            self.controller.delete_class(uid=self.uid, change_classes_uid=new_uid, redraw=True)
        self.grab_release()
        self.destroy()


class ClassItem(ctk.CTkFrame):
    """A single class item in the classes container.

    The item has the following components:
    - Text entry for the class name.
    - Radio button to set the default class.
    - Button to choose the class color.
    - Button to delete the class.

    Args:
        master: The parent widget.
        controller: The controller object.
        class_name: The name of the class.
        class_color: The color of the class.
        default_class_uid: The UID of the default class.
        uid: The UID of the class.
        delete_callback: The callback function to call when the class is deleted.
    """

    def __init__(
        self,
        master,
        controller: Controller,
        class_name: str,
        class_color: str,
        default_class_uid: IntVar,
        uid: int,
        delete_callback: Callable,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)

        self.controller = controller

        self.class_name = StringVar(value=class_name)

        self.delete_callback = delete_callback
        self.uid = uid

        self.entry = ctk.CTkEntry(self, textvariable=self.class_name)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.radio = ctk.CTkRadioButton(self, text="", variable=default_class_uid, value=uid)
        self.radio.pack(side="left", padx=(10, 10))

        self.color_button = ctk.CTkButton(
            self, text="", width=20, fg_color=class_color, command=self.choose_color
        )
        self.color_button.pack(side="left", padx=(10, 10))

        self.delete_button = ctk.CTkButton(self, text="X", command=self.delete_item)
        self.delete_button.pack(side="left", padx=(10, 10))

    def choose_color(self) -> None:
        """Open a color chooser dialog to choose a color for the class."""
        color_code = colorchooser.askcolor(title="Choose color")[1]
        if color_code:
            self.color_button.configure(fg_color=color_code)
            self.controller.change_class_color(self.uid, color_code)

    def delete_item(self) -> None:
        """Delete the class."""
        self.delete_callback(self)


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
        popup = ClassDeletionPopup(self, self.controller, del_item.uid)
        self.wait_window(popup)
        if del_item.uid not in self.controller.available_class_uids():
            del_item.pack_forget()
            self.class_items.remove(del_item)

    def update_default_uid(self, *args) -> None:
        """Update the default class UID in the controller."""
        self.controller.set_default_class_uid(self.default_class_uid.get())


class ClassesPopup(ctk.CTkToplevel):
    """Popup window for managing classes.

    The user can add, delete, and change the name and color of classes.

    Args:
        master: The parent widget.
        controller: The controller object.
    """

    def __init__(self, master, controller: Controller, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title("Classes")
        self.geometry("400x400")
        self.controller = controller

        self.container = ctk.CTkFrame(self, fg_color=self.cget("fg_color"))
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        self.warning_label = ctk.CTkLabel(self.container, text="", text_color="red")
        self.warning_label.pack(pady=(0, 10))

        self.classes_container = ClassesContainer(self.container, self.controller, self.can_delete)
        self.classes_container.pack(fill="both", expand=True, pady=(0, 20))

        self.add_class_button = ctk.CTkButton(self.container, text="Add Class", command=self.add_class)
        self.add_class_button.pack(side="left", padx=(0, 10))

        self.done_button = ctk.CTkButton(self.container, text="Done", command=self.on_done)
        self.done_button.pack(side="right")

        # Make the popup modal
        self.grab_set()
        self.transient(master)
        self.focus_set()

    def add_class(self) -> None:
        """Add a new class to the container."""
        new_class = self.controller.add_new_init_class()
        self.classes_container.add_class_item(new_class["name"], new_class["color"], new_class["uid"])

    def can_delete(self, uid: int) -> bool:
        """Check if a class can be deleted.

        A class cannot be deleted if it is the last class or the default class. In this case, a warning
        message is displayed.

        Args:
            uid: The unique identifier of the class.

        Returns:
            bool: True if the class can be deleted, False otherwise.
        """
        if self.controller.get_number_classes() == 1:
            self.warning_label.configure(text="Cannot delete the last class.")
            return False
        if self.controller.get_default_class_uid() == uid:
            self.warning_label.configure(text="Cannot delete the default class.")
            return False
        return True

    def on_done(self) -> None:
        """Close the popup and save the changes to the classes.

        Checks if there are two classes with the same name. If there are, a warning message is displayed and
        the changes are not saved.
        """
        class_names = [item.class_name.get() for item in self.classes_container.class_items]
        if len(class_names) != len(set(class_names)):
            self.warning_label.configure(text="Cannot have two classes with the same name.")
            return

        uids = [item.uid for item in self.classes_container.class_items]
        self.controller.change_class_name(uids, class_names)

        self.grab_release()
        self.destroy()
