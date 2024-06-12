"""Content module for the annotator application."""

import customtkinter as ctk
from PIL import Image, ImageTk

from annotator.controller import Controller

BOX_COLOR = "red"


class Content(ctk.CTkFrame):
    """Main content frame for the annotator application.

    Args:
        master: The parent widget.
        annotation_store: The annotation store object to use for image data.
    """

    def __init__(self, master, controller: Controller, initial_size: tuple[int, int], **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller

        self.canvas = ctk.CTkCanvas(self)
        self.canvas.pack(fill="both", expand=True)

        self.available_width, self.available_height = initial_size

        # setup image
        self.original_image: Image.Image
        self.image: Image.Image
        self.tk_image: ImageTk.PhotoImage
        self.new_image()

        # setup mouse event params
        self.mouse_down: bool = False
        self.start_x: int
        self.start_y: int
        self.current_box: int
        self.zoom_level: float = 1.0
        self.zoom_center: tuple = (0, 0)

        # listen to mouse events
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Configure>", self._on_configure)

    def update(self) -> None:
        """Update the content area with the current image and bounding boxes."""
        self.refresh_boxes()

    def refresh_boxes(self) -> None:
        """Refresh the bounding boxes on the canvas."""
        self.canvas.delete("box")

        cur_zoom = self.zoom_level
        cur_center_x, cur_center_y = self.zoom_center
        half_img_size_x = self.img_width / 2
        half_img_size_y = self.img_height / 2

        for box, label in zip(self.controller.current_boxes(), self.controller.current_labels()):
            x1, y1, x2, y2 = self._map_box_to_img(box, (self.img_width, self.img_height))

            # Adjust the coordinates based on the current zoom and center
            adj_x1 = (x1 * cur_zoom) - (cur_center_x - half_img_size_x)
            adj_y1 = (y1 * cur_zoom) - (cur_center_y - half_img_size_y)
            adj_x2 = (x2 * cur_zoom) - (cur_center_x - half_img_size_x)
            adj_y2 = (y2 * cur_zoom) - (cur_center_y - half_img_size_y)

            self.canvas.create_rectangle(adj_x1, adj_y1, adj_x2, adj_y2, outline=BOX_COLOR, tags="box")
            self.canvas.create_text(adj_x1, adj_y1 - 14, text=label, anchor="nw", fill=BOX_COLOR, tags="box")

    def new_image(self) -> None:
        """Load a new image into the content area."""
        try:
            self.zoom_level = 1
            self.image = Image.open(self.controller.current_file_path())
            self.img_width, self.img_height = self.image.size

            # Resize the image to fit the available space
            if self.img_width > self.available_width:
                ratio = self.available_width / self.img_width
                self.img_width = self.available_width
                self.img_height = int(self.img_height * ratio)
            if self.img_height > self.available_height:
                ratio = self.available_height / self.img_height
                self.img_height = self.available_height
                self.img_width = int(self.img_width * ratio)

            self.image = self.image.resize((self.img_width, self.img_height))

            self.zoom_center = (self.img_width // 2, self.img_height // 2)
            self.canvas.config(width=self.img_width, height=self.img_height)
            self.original_image = self.image.copy()
            self.tk_image = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
            self.refresh_boxes()
        except Exception as e:
            # raise e
            print(f"Failed to load image {self.controller.current_file_path()}: {e}")
            self.canvas.delete("all")
            self.canvas.create_text(
                0,
                0,
                text=f"Failed to load image {self.controller.current_file_path()}",
                fill="red",
                font=("Arial", 24),
            )

    def zoom(self) -> None:
        if self.image is None:
            return

        new_width = int(self.img_width * self.zoom_level)
        new_height = int(self.img_height * self.zoom_level)
        zoomed_image = self.original_image.resize((new_width, new_height))

        # adjust the zoom center to the new size
        cx, cy = self.zoom_center

        # calculate the cropping box to the center and the zoom position
        half_view_size_x = self.img_width // 2
        half_view_size_y = self.img_height // 2

        crop_x1 = int(cx - half_view_size_x)
        crop_y1 = int(cy - half_view_size_y)
        crop_x2 = int(cx + half_view_size_x)
        crop_y2 = int(cy + half_view_size_y)

        self.image = zoomed_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.refresh_boxes()

    def _on_mouse_down(self, event) -> None:
        """Handle the mouse down event on the canvas. Create a new bounding box."""
        self.mouse_down = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_box = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline=BOX_COLOR, tags="box"
        )

    def _on_mouse_move(self, event) -> None:
        """Handle the mouse move event on the canvas. Resize the current bounding box."""
        if not self.mouse_down:
            return

        self.canvas.coords(
            self.current_box,
            self.start_x,
            self.start_y,
            self.canvas.canvasx(event.x),
            self.canvas.canvasy(event.y),
        )

    def _on_mouse_up(self, event) -> None:
        """Handle the mouse up event on the canvas. Save the bounding box."""
        if not self.mouse_down:
            return

        x1, y1, x2, y2 = (
            self.start_x,
            self.start_y,
            self.canvas.canvasx(event.x),
            self.canvas.canvasy(event.y),
        )

        # Adjust the coordinates based on the current zoom and center
        cur_zoom = self.zoom_level
        cur_center_x, cur_center_y = self.zoom_center
        half_img_size_x = self.img_width // 2
        half_img_size_y = self.img_height // 2

        x1 = (x1 + (cur_center_x - half_img_size_x)) / cur_zoom
        y1 = (y1 + (cur_center_y - half_img_size_y)) / cur_zoom
        x2 = (x2 + (cur_center_x - half_img_size_x)) / cur_zoom
        y2 = (y2 + (cur_center_y - half_img_size_y)) / cur_zoom

        # Ensure the box is in format [center_x, center_y, width, height], all values in [0, 1]
        x1, y1, x2, y2 = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
        center_x = (x1 + x2) / 2 / self.img_width
        center_y = (y1 + y2) / 2 / self.img_height
        width = (x2 - x1) / self.img_width
        height = (y2 - y1) / self.img_height

        self.controller.add_box((center_x, center_y, width, height))
        self.mouse_down = False

    def _on_mouse_wheel(self, event):
        # If the mouse is down, don't zoom
        if self.mouse_down:
            return

        # Get mouse position relative to the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Ensure the mouse is inside the image
        if x < 0 or x >= self.img_width or y < 0 or y >= self.img_height:
            return

        # Calculate the current image size
        cur_img_size_x = self.img_width * self.zoom_level
        cur_img_size_y = self.img_height * self.zoom_level

        # Calculate the position of the cursor relative to the whole image
        rel_x = (x + (self.zoom_center[0] - self.img_width / 2)) / cur_img_size_x
        rel_y = (y + (self.zoom_center[1] - self.img_height / 2)) / cur_img_size_y

        # Zoom in or out
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1

        # Limit the zoom level
        self.zoom_level = max(1.0, min(self.zoom_level, 10.0))

        # Calculate the new image size
        new_img_size_x = self.img_width * self.zoom_level
        new_img_size_y = self.img_height * self.zoom_level

        # Adjust the zoom center based on the relative position of the cursor
        self.zoom_center = (
            rel_x * new_img_size_x - (x - self.img_width / 2),
            rel_y * new_img_size_y - (y - self.img_height / 2),
        )

        if self.zoom_level == 1:
            self.zoom_center = (self.img_width // 2, self.img_height // 2)

        self.zoom()
        self.refresh_boxes()

    def _map_box_to_img(self, box: tuple[float, float, float, float], img_size: tuple[int, int]):
        """Map a bounding box from the canvas to the image.

        Args:
            box: The bounding box to map. Format: [center_x, center_y, width, height], all values in [0, 1].
            img_size: The size of the image.

        Returns:
            The mapped bounding box in the format [x1, y1, x2, y2].
        """
        center_x, center_y, width, height = box
        img_width, img_height = img_size

        x1 = (center_x - width / 2) * img_width
        y1 = (center_y - height / 2) * img_height
        x2 = (center_x + width / 2) * img_width
        y2 = (center_y + height / 2) * img_height

        return x1, y1, x2, y2

    def _on_configure(self, _):
        available_width = self.master.winfo_width() - 400
        available_height = self.master.winfo_height() - 50
        if available_width != self.available_width or available_height != self.available_height:
            self.available_width = available_width
            self.available_height = available_height
            self.new_image()
