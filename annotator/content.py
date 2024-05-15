"""Content module for the annotator application."""

import customtkinter as ctk
from PIL import Image, ImageTk

from annotator.annotation_store import AnnotationStore


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

        self.canvas = ctk.CTkCanvas(self, width=640, height=640)
        self.canvas.pack(fill="both", expand=True)

        # listen to mouse events
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def update(self):
        """Update the content area with the current image and bounding boxes."""
        img = Image.open(self.annotation_store.file_path)
        img = img.resize((640, 640))  # Resize to fit the display area
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.refresh_boxes()

    def refresh_boxes(self):
        """Refresh the bounding boxes on the canvas."""
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        for box, label in zip(self.annotation_store.boxes, self.annotation_store.labels):
            x1, y1, x2, y2 = box
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red")
            self.canvas.create_text(x1, y1 - 14, text=label, anchor="nw", fill="red")

    def _on_mouse_down(self, event):
        """Handle the mouse down event on the canvas. Create a new bounding box."""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_box = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="red"
        )

    def _on_mouse_move(self, event):
        """Handle the mouse move event on the canvas. Resize the current bounding box."""
        self.canvas.coords(
            self.current_box,
            self.start_x,
            self.start_y,
            self.canvas.canvasx(event.x),
            self.canvas.canvasy(event.y),
        )

    def _on_mouse_up(self, event):
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
