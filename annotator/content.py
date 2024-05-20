"""Content module for the annotator application."""

import customtkinter as ctk
from PIL import Image, ImageTk

from annotator.annotation_store import AnnotationStore


IMG_SIZE = 640
BOX_COLOR = "red"


class Content(ctk.CTkFrame):
    """Main content frame for the annotator application.

    Args:
        master: The parent widget.
        annotation_store: The annotation store object to use for image data.
    """
    def __init__(self, master, annotation_store: AnnotationStore, **kwargs):
        super().__init__(master, **kwargs)
        self._main_frame = master
        self.annotation_store = annotation_store

        self.canvas = ctk.CTkCanvas(self, width=IMG_SIZE, height=IMG_SIZE)
        self.canvas.pack(fill="both", expand=True)

        # setup image
        self.original_image: Image.Image
        self.image: Image.Image
        self.tk_image: ImageTk.PhotoImage
        self.new_image()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        # setup mouse event params
        self.mouse_down: bool = False
        self.start_x: int
        self.start_y: int
        self.current_box: int
        self.zoom_level: int = 1
        self.zoom_center: tuple = (IMG_SIZE // 2, IMG_SIZE // 2)

        # listen to mouse events
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

    def update(self) -> None:
        """Update the content area with the current image and bounding boxes."""
        self.refresh_boxes()

    def refresh_boxes(self) -> None:
        """Refresh the bounding boxes on the canvas."""
        self.canvas.delete("box")

        cur_zoom = self.zoom_level
        cur_center_x, cur_center_y = self.zoom_center
        half_img_size = IMG_SIZE / 2

        for box, label in zip(self.annotation_store.boxes, self.annotation_store.labels):
            x1, y1, x2, y2 = box

            # Adjust the coordinates based on the current zoom and center
            adj_x1 = (x1 * cur_zoom) - (cur_center_x - half_img_size)
            adj_y1 = (y1 * cur_zoom) - (cur_center_y - half_img_size)
            adj_x2 = (x2 * cur_zoom) - (cur_center_x - half_img_size)
            adj_y2 = (y2 * cur_zoom) - (cur_center_y - half_img_size)

            self.canvas.create_rectangle(adj_x1, adj_y1, adj_x2, adj_y2, outline=BOX_COLOR, tags="box")
            self.canvas.create_text(adj_x1, adj_y1 - 14, text=label, anchor="nw", fill=BOX_COLOR, tags="box")


    def new_image(self) -> None:
        """Load a new image into the content area."""
        try:
            self.zoom_level = 1
            self.zoom_center = (IMG_SIZE // 2, IMG_SIZE // 2)
            self.image = Image.open(self.annotation_store.file_path)
            self.image = self.image.resize((IMG_SIZE, IMG_SIZE))
            self.original_image = self.image.copy()
            self.tk_image = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        except Exception as e:
            print(f"Failed to load image {self.annotation_store.file_path}: {e}")
            self.canvas.delete("all")
            self.canvas.create_text(
                IMG_SIZE // 2, IMG_SIZE // 2, text=f"Failed to load image {self.annotation_store.file_path}", fill="red", font=("Arial", 24)
            )

    def zoom(self) -> None:
        if self.image is None:
            return
        
        new_width = int(IMG_SIZE * self.zoom_level)
        new_height = int(IMG_SIZE * self.zoom_level)
        zoomed_image = self.original_image.resize((new_width, new_height))

        # adjust the zoom center to the new size
        cx, cy = self.zoom_center

        # calculate the cropping box to the center and the zoom position
        half_view_size = IMG_SIZE // 2

        crop_x1 = int(cx - half_view_size)
        crop_y1 = int(cy - half_view_size)
        crop_x2 = int(cx + half_view_size)
        crop_y2 = int(cy + half_view_size)

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
        self.canvas.coords(
            self.current_box,
            self.start_x,
            self.start_y,
            self.canvas.canvasx(event.x),
            self.canvas.canvasy(event.y),
        )

    def _on_mouse_up(self, event) -> None:
        """Handle the mouse up event on the canvas. Save the bounding box."""
        x1, y1, x2, y2 = (
            self.start_x,
            self.start_y,
            self.canvas.canvasx(event.x),
            self.canvas.canvasy(event.y),
        )

        # Adjust the coordinates based on the current zoom and center
        cur_zoom = self.zoom_level
        cur_center_x, cur_center_y = self.zoom_center
        half_img_size = IMG_SIZE / 2

        x1 = (x1 + (cur_center_x - half_img_size)) / cur_zoom
        y1 = (y1 + (cur_center_y - half_img_size)) / cur_zoom
        x2 = (x2 + (cur_center_x - half_img_size)) / cur_zoom
        y2 = (y2 + (cur_center_y - half_img_size)) / cur_zoom

        self.annotation_store.add_box((x1, y1, x2, y2))
        self.refresh_boxes()
        self._main_frame.right_sidebar.update()
        self.mouse_down = False

    def _on_mouse_wheel(self, event):
        # If the mouse is down, don't zoom
        if self.mouse_down:
            return

        # Get mouse position relative to the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Ensure the mouse is inside the image
        if x < 0 or x >= IMG_SIZE or y < 0 or y >= IMG_SIZE:
            return

        # Calculate the current image size
        cur_img_size = IMG_SIZE * self.zoom_level

        # Calculate the position of the cursor relative to the whole image
        rel_x = (x + (self.zoom_center[0] - IMG_SIZE / 2)) / cur_img_size
        rel_y = (y + (self.zoom_center[1] - IMG_SIZE / 2)) / cur_img_size

        # Zoom in or out
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1

        # Limit the zoom level
        self.zoom_level = max(1.0, min(self.zoom_level, 10.0))

        # Calculate the new image size
        new_img_size = IMG_SIZE * self.zoom_level

        # Adjust the zoom center based on the relative position of the cursor
        self.zoom_center = (
            rel_x * new_img_size - (x - IMG_SIZE / 2),
            rel_y * new_img_size - (y - IMG_SIZE / 2)
        )

        if self.zoom_level == 1:
            self.zoom_center = (IMG_SIZE // 2, IMG_SIZE // 2)

        self.zoom()
        self.refresh_boxes()
