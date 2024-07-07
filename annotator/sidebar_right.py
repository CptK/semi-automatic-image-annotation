"""Right sidebar for the annotator GUI."""

import customtkinter as ctk

from annotator.controller import Controller


class RightSidebarList(ctk.CTkScrollableFrame):
    """List of labels for the right sidebar.

    Args:
        master: The parent widget.
        annotation_store: The annotation store object to use for image data.
        main_frame: The main frame object.
    """

    def __init__(self, master, controller: Controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.update()

    def update(self):
        """Update the list of labels in the sidebar."""
        for widget in self.winfo_children():
            widget.destroy()

        for i, label_uid in enumerate(self.controller.current_label_uids()):
            label = self.controller.get_class_name(label_uid)

            # add ComboBox for each label
            frame = ctk.CTkFrame(self)
            frame.pack(fill="x", pady=5, padx=5)

            id_label = ctk.CTkLabel(frame, text=f"{i}.")
            id_label.pack(side="left", fill="x", expand=True, padx=(0, 5))

            # Add ComboBox for each label inside the frame
            label_option = ctk.CTkComboBox(
                frame,
                values=self.controller.available_labels(),
                command=lambda choice, idx=i: self.change_label(choice, idx),
            )
            label_option.set(label)
            label_option.pack(side="left", fill="x", expand=True)  # Pack to the left and allow expansion

            # Add a delete button next to the ComboBox
            del_button = ctk.CTkButton(frame, text="X", width=10, command=lambda idx=i: self.delete(idx))
            del_button.pack(side="right", padx=(10, 0))  # Pack to the right of the ComboBox

    def change_label(self, label, idx):
        """Change the label for the given index."""
        label_uid = self.controller.get_class_uid(label)
        self.controller.change_label(idx, label_uid)

    def delete(self, idx):
        """Delete the label for the given index."""
        self.controller.delete(idx)
        self.update()


class RightSidebar(ctk.CTkFrame):
    """Right sidebar for the annotator GUI.

    Args:
        master: The parent widget.
        annotation_store: The annotation store object to use for image data.
    """

    def __init__(self, master, controller: Controller, **kwargs):
        super().__init__(master, **kwargs)
        self._main_frame = master
        self.controller = controller
        self.setup()

    def setup(self):
        """Set up the right sidebar layout."""
        next_button = ctk.CTkButton(self, text="Next", command=self.controller.next)
        next_button.pack(pady=(20, 0), padx=5, fill="x")

        skip_button = ctk.CTkButton(self, text="Skip")
        skip_button.pack(pady=(10, 20), padx=5, fill="x")

        # add checkbox and label for marking the image as ready
        ready_var = ctk.BooleanVar()
        ready_var.set(self.controller.ready())
        ready_checkbox = ctk.CTkCheckBox(
            self, text="Mark as ready", variable=ready_var, command=self.mark_ready
        )
        ready_checkbox.pack(pady=(10, 20), padx=5, fill="x")

        self.item_list = RightSidebarList(self, self.controller)
        self.item_list.pack(fill="both", expand=True)

    def update(self):
        """Update the right sidebar layout."""
        self.item_list.update()

    def mark_ready(self):
        """Mark the current image as ready."""
        self.controller.mark_ready()
