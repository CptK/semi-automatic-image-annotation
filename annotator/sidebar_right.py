"""Right sidebar for the annotator GUI."""

import customtkinter as ctk

from annotator.controller import Controller


class RightSidebarList(ctk.CTkScrollableFrame):
    """List of labels for the right sidebar.

    Args:
        master: The parent widget.
        controller: The controller object.
        main_frame: The main frame object.
    """

    def __init__(self, master, controller: Controller, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.controller = controller
        self.update()

    def update(self) -> None:
        """Update the list of labels in the sidebar."""
        for widget in self.winfo_children():
            widget.destroy()

        current_img = self.controller.current()
        if current_img is None:
            return

        for i, label_uid in enumerate(current_img.label_uids):
            label = self.controller.get_class_name(label_uid)

            # add ComboBox for each label
            frame = ctk.CTkFrame(self, fg_color=self.cget("fg_color"))
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

    def change_label(self, label: str, idx: int) -> None:
        """Change the label for the given index."""
        label_uid = self.controller.get_class_uid(label)
        self.controller.change_image_annotation(idx, label_uid=label_uid)

    def delete(self, idx: int):
        """Delete the label for the given index."""
        self.controller.delete(idx)
        self.update()


class RightSidebar(ctk.CTkFrame):
    """Right sidebar for the annotator GUI.

    Args:
        master: The parent widget.
        controller: The controller object.
    """

    def __init__(self, master, controller: Controller, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._main_frame = master
        self.controller = controller
        self.setup()

    def setup(self) -> None:
        """Set up the right sidebar layout."""
        next_button = ctk.CTkButton(self, text="Next", command=self.controller.next)
        next_button.pack(pady=(20, 0), padx=5, fill="x")

        del_button = ctk.CTkButton(self, text="Delete", command=self.controller.delete_image)
        del_button.pack(pady=(10, 20), padx=5, fill="x")

        # add checkbox and label for marking the image as ready
        self.ready_var = ctk.BooleanVar()
        self.ready_var.set(self.controller.is_ready(self.controller.active_uuid()))
        ready_checkbox = ctk.CTkCheckBox(
            self, text="Mark as ready", variable=self.ready_var, command=self.mark_ready
        )
        ready_checkbox.pack(pady=(10, 20), padx=5, fill="x")

        self.item_list = RightSidebarList(self, self.controller, fg_color=self.cget("fg_color"))
        self.item_list.pack(fill="both", expand=True)

    def update(self) -> None:
        """Update the right sidebar layout."""
        self.item_list.update()
        self.ready_var.set(self.controller.is_ready(self.controller.active_uuid()))

    def mark_ready(self) -> None:
        """Mark the current image as ready."""
        self.controller.mark_ready()
