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
        self.image: Image.Image
        self.tk_image: ImageTk.PhotoImage
        self.new_image()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        # listen to mouse events
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def update(self) -> None:
        """Update the content area with the current image and bounding boxes."""
        self.refresh_boxes()

    def refresh_boxes(self) -> None:
        """Refresh the bounding boxes on the canvas."""
        self.canvas.delete("box")

        for box, label in zip(self.annotation_store.boxes, self.annotation_store.labels):
            x1, y1, x2, y2 = box
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=BOX_COLOR, tags="box")
            self.canvas.create_text(x1, y1 - 14, text=label, anchor="nw", fill=BOX_COLOR, tags="box")

    def new_image(self) -> None:
        """Load a new image into the content area."""
        try:
            print(self.annotation_store.file_path)
            self.image = Image.open(self.annotation_store.file_path)
            self.image = self.image.resize((IMG_SIZE, IMG_SIZE))
            self.tk_image = ImageTk.PhotoImage(self.image)
        except Exception as e:
            print(f"Failed to load image {self.annotation_store.file_path}: {e}")
            self.canvas.delete("all")
            self.canvas.create_text(
                IMG_SIZE // 2, IMG_SIZE // 2, text=f"Failed to load image {self.annotation_store.file_path}", fill="red", font=("Arial", 24)
            )
        
    def _on_mouse_down(self, event) -> None:
        """Handle the mouse down event on the canvas. Create a new bounding box."""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_box = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline=BOX_COLOR
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
        self.annotation_store.add_box((x1, y1, x2, y2))
        self.refresh_boxes()
        self._main_frame.right_sidebar.update()
