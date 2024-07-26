"""Left sidebar for the annotator GUI."""

import os
from collections.abc import Callable
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

from annotator.controller import Controller


class ListButton(ctk.CTkButton):
    """Button for the left sidebar list items.

    Args:
        master: The parent widget.
        text: The text to display on the button.
        command: The command to call when the button is clicked.
        active: Whether the button is currently active.
    """

    def __init__(self, master, text, command, active: bool = False, **kwargs) -> None:
        text_color = "black" if active else "gray"
        super().__init__(
            master,
            text=text,
            command=command,
            fg_color="transparent",
            text_color=text_color,
            height=8,
            **kwargs,
        )

    def update(self, active: bool) -> None:
        """Update the button appearance based on the active status.

        Args:
            active: Whether the button is currently active.
        """
        text_color = "black" if active else "gray"
        self.configure(text_color=text_color)


class ListItem(ctk.CTkFrame):
    """List item for the left sidebar.

    Args:
        master: The parent widget.
        text: The text to display on the list item.
        command: The command to call when the item is clicked.
        active: Whether the item is currently active.
        ready: Whether the item is marked as ready.
    """

    def __init__(self, master, text: str, command: Callable, active: bool, ready: bool, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.button = ListButton(self, text=text, command=command, active=active)
        label_text = "✓" if ready else " "
        self.label = ctk.CTkLabel(
            self, text=label_text, fg_color="transparent", text_color="green", font=("Arial", 12)
        )
        self.label.pack(side="right", padx=5)
        self.button.pack(fill="x", padx=5, pady=5)

    def update(self, active, ready) -> None:
        """Update the list item appearance based on the active status and readiness.

        Args:
            active: Whether the item is currently active.
            ready: Whether the item is marked as ready.
        """
        text = "✓" if ready else " "
        self.label.configure(text=text)
        self.button.update(active)


class LeftSidebarList(ctk.CTkScrollableFrame):
    """Left sidebar list for the annotator application.

    Args:
        master: The parent widget.
        controller: The controller object.
    """

    def __init__(self, master, controller: Controller, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.controller = controller
        self.setup()

    def setup(self) -> None:
        """Set up the left sidebar list items."""
        self.list_items: list[ListItem] = []
        for i, name in enumerate(self.controller.image_names()):
            button = ListItem(
                self,
                text=name,
                command=lambda i=i: self.controller.jump_to(i),
                active=i == self.controller.current_index(),
                ready=self.controller[i].ready,
            )
            button.pack(fill="x", padx=5, pady=5)
            self.list_items.append(button)

    def update(self) -> None:
        """Update the left sidebar list items."""
        if len(self.list_items) == len(self.controller.image_names()):
            for i, list_item in enumerate(self.list_items):
                list_item.update(
                    active=i == self.controller.current_index(),
                    ready=self.controller[i].ready,
                )
        else:
            for item in self.list_items:
                item.destroy()
            self.setup()

    def add_items(self, names: list[str], idx: list[int]) -> None:
        """Add items to the left sidebar list.

        Args:
            names: A list of file names to add.
            idx: A list of indices to add.
        """
        for i, name in zip(idx, names):
            button = ListItem(
                self,
                text=name,
                command=lambda i=i: self.controller.jump_to(i),
                active=i == self.controller.current_index(),
                ready=self.controller[i].ready,
            )
            button.pack(fill="x", padx=5, pady=5)
            self.list_items.insert(i, button)


class LeftSidebar(ctk.CTkFrame):
    """Left Sidebar of the annotator application containing a list of all files and a button for adding more.

    Args:
        master: The parent widget.
        controller: The controller object.
    """

    EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]

    def __init__(self, master, controller: Controller, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.controller = controller
        self.setup()

    def setup(self) -> None:
        self.list = LeftSidebarList(self, self.controller)
        self.list.pack(fill="both", expand=True)

        self.button_frame = ctk.CTkFrame(self, fg_color="transparent", bg_color="transparent")
        self.button_frame.pack(fill="x", padx=5, pady=5)

        self.add_images_button = ctk.CTkButton(
            self.button_frame,
            image=ctk.CTkImage(Image.open("./assets/add_image.png").resize((40, 40))),
            compound="left",
            command=self._select_images,
            fg_color="transparent",
            bg_color="transparent",
            text_color="white",
            text="",
            height=40,
        )
        self.add_images_button.pack(side="left", padx=5, pady=5)

        self.add_directory_button = ctk.CTkButton(
            self.button_frame,
            image=ctk.CTkImage(Image.open("./assets/new_folder.png").resize((40, 40))),
            compound="left",
            command=self._select_directory,
            fg_color="transparent",
            bg_color="transparent",
            text_color="white",
            text="",
            height=40,
        )
        self.add_directory_button.pack(side="right", fill="x", padx=5, pady=5)

    def update(self) -> None:
        """Update the left sidebar."""
        self.list.update()

    def _select_images(self) -> None:
        """Select images to add to the annotation tool.

        Opens a file dialog to select an image, multiple images or a directory of images.

        Returns:
            a list of selected image file paths.
        """
        files = filedialog.askopenfilenames(
            title="Select Image(s)",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif")],
        )
        self._add_images(list(files))

    def _select_directory(self) -> None:
        """Select a directory of images to add to the annotation tool.

        Opens a file dialog to select a directory of images.
        """
        directory = filedialog.askdirectory(title="Select Directory")
        images = self.find_all_images(directory, self.EXTENSIONS)
        self._add_images(images)

    def _add_images(self, files: list[str]) -> None:
        """Add images to the annotation tool.

        Args:
            files: A list of image file paths to add.
        """
        n_old_images = len(self.controller.image_names())
        self.controller.add_images(files)
        new_indices = list(range(n_old_images, len(self.controller.image_names())))
        self.list.add_items([os.path.basename(file) for file in files], new_indices)

    def find_all_images(self, root_dir: str, extensions: list[str]) -> list[str]:
        """Find all images in a directory and its subdirectories.

        Args:
            root_dir: The root directory to search.
            extensions: A list of image file extensions to search for.

        Returns:
            A list of image file paths.
        """
        # add all images in the root directory to the list, for all subdirectories, call function recursively
        image_paths = []
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    image_paths.append(os.path.join(root, file))
            for dir in dirs:
                image_paths.extend(self.find_all_images(os.path.join(root, dir), extensions))
        return image_paths
