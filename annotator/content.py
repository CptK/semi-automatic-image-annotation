"""Content module for the annotator application."""

from enum import Enum

import customtkinter as ctk
from PIL import Image, ImageTk

from annotator.bounding_box import BoundingBox
from annotator.controller import Controller


class ImageContent(ImageTk.PhotoImage):

    def __init__(self, image_path: str, initial_size: tuple[int, int], **kwargs):
        self.available_width, self.available_height = initial_size
        self.original_image = Image.open(image_path)
        self.image = self.original_image.copy()
        self.img_width, self.img_height = self.calc_fit_size(self.original_image.size)
        self.image = self.original_image.copy().resize((self.img_width, self.img_height))

        super().__init__(self.image, **kwargs)

        # zooming parameters
        self.zoom_level: float = 1.0
        self.zoom_center: tuple = (self.img_width // 2, self.img_height // 2)

    def calc_fit_size(self, image_size: tuple[int, int]) -> tuple[int, int]:
        img_width, img_height = image_size

        # Resize the image to fit the available space
        if img_width > self.available_width:
            ratio = self.available_width / img_width
            img_width = self.available_width
            img_height = int(img_height * ratio)
        if img_height > self.available_height:
            ratio = self.available_height / img_height
            img_height = self.available_height
            img_width = int(img_width * ratio)

        return img_width, img_height

    def configure(self, available_width: int, available_height: int) -> None:
        self.available_width = available_width
        self.available_height = available_height
        self.img_width, self.img_height = self.calc_fit_size(self.original_image.size)
        self.image = self.image.resize((self.img_width, self.img_height))
        self.paste(self.image)

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
        self.paste(self.image)

    def on_mouse_wheel(self, event_x, event_y, event_delta):
        # Ensure the mouse is inside the image
        if event_x < 0 or event_x >= self.img_width or event_y < 0 or event_y >= self.img_height:
            return

        # Calculate the current image size
        cur_img_size_x = self.img_width * self.zoom_level
        cur_img_size_y = self.img_height * self.zoom_level

        # Calculate the position of the cursor relative to the whole image
        rel_x = (event_x + (self.zoom_center[0] - self.img_width / 2)) / cur_img_size_x
        rel_y = (event_y + (self.zoom_center[1] - self.img_height / 2)) / cur_img_size_y

        # Zoom in or out
        if event_delta > 0:
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
            rel_x * new_img_size_x - (event_x - self.img_width / 2),
            rel_y * new_img_size_y - (event_y - self.img_height / 2),
        )

        if self.zoom_level == 1:
            self.zoom_center = (self.img_width // 2, self.img_height // 2)

        self.zoom()


class Content(ctk.CTkFrame):
    """Main content frame for the annotator application.

    Args:
        master: The parent widget.
        annotation_store: The annotation store object to use for image data.
    """

    class EventState(Enum):
        IDLE = 0
        DRAWING = 1
        RESIZING = 2

    def __init__(self, master, controller: Controller, initial_size: tuple[int, int], **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.canvas = ctk.CTkCanvas(self)
        self.canvas.pack(fill="both", expand=True)
        self.available_width, self.available_height = initial_size
        self.state = self.EventState.IDLE

        self.image_content: ImageContent
        self.bboxes: list[BoundingBox] = []
        self.new_image()
        self._create_bounding_boxes()

        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._on_mouse_click)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)

    def update(self) -> None:
        """Update the content area."""
        self.new_image()
        self._create_bounding_boxes()

    def new_image(self) -> None:
        """Load a new image into the content area."""
        try:
            self.image_content = ImageContent(
                self.controller.current_file_path(), (self.available_width, self.available_height)
            )
            self.canvas.config(width=self.image_content.img_width, height=self.image_content.img_height)
            self.canvas.create_image(0, 0, anchor="nw", image=self.image_content)
            self.canvas.lower(self.image_content)

        except Exception as e:
            print(f"Failed to load image {self.controller.current_file_path()}: {e}")
            self.canvas.delete("all")
            self.canvas.create_text(
                0,
                0,
                text=f"Failed to load image {self.controller.current_file_path()}",
                fill="red",
                font=("Arial", 24),
            )

    def relative_to_canvas_coords(self, box):
        center_x, center_y, width, height = box
        img_width, img_height = self.image_content.img_width, self.image_content.img_height
        zoom_center = self.image_content.zoom_center
        zoom_level = self.image_content.zoom_level

        # adjust bounding box to original image size
        x1 = (center_x - width / 2) * img_width
        y1 = (center_y - height / 2) * img_height
        x2 = (center_x + width / 2) * img_width
        y2 = (center_y + height / 2) * img_height

        # adjust bounding box to zoomed image size
        x1 = (x1 * zoom_level) - (zoom_center[0] - img_width / 2)
        y1 = (y1 * zoom_level) - (zoom_center[1] - img_height / 2)
        x2 = (x2 * zoom_level) - (zoom_center[0] - img_width / 2)
        y2 = (y2 * zoom_level) - (zoom_center[1] - img_height / 2)

        return x1, y1, x2, y2

    def canvas_to_relative_coords(self, canvas_coords):
        x1, y1, x2, y2 = canvas_coords
        img_width, img_height = self.image_content.img_width, self.image_content.img_height
        zoom_center = self.image_content.zoom_center
        zoom_level = self.image_content.zoom_level

        # adjust bounding box to unzoomed image size
        x1 = (x1 + (zoom_center[0] - img_width / 2)) / zoom_level
        y1 = (y1 + (zoom_center[1] - img_height / 2)) / zoom_level
        x2 = (x2 + (zoom_center[0] - img_width / 2)) / zoom_level
        y2 = (y2 + (zoom_center[1] - img_height / 2)) / zoom_level

        # adjust bounding box to original image size
        center_x = ((x1 + x2) / 2) / img_width
        center_y = ((y1 + y2) / 2) / img_height
        width = (x2 - x1) / img_width
        height = (y2 - y1) / img_height

        return center_x, center_y, width, height

    def _create_bounding_boxes(self):
        self.canvas.delete("bbox")
        self.canvas.delete("handle")
        self.bboxes = []

        for i, (box, label) in enumerate(
            zip(self.controller.current_boxes(), self.controller.current_labels())
        ):
            box = self.relative_to_canvas_coords(box)
            on_resize_end_callback = lambda idx=i: self.controller.change_box(  # noqa: E731
                idx, self.canvas_to_relative_coords(self.bboxes[idx].get_box()), redraw=False
            )
            bbox = BoundingBox(self.canvas, box, label, self.controller.classes_store(), on_resize_end_callback, i)
            self.bboxes.append(bbox)

    def _update_bounding_boxes(self):
        for bbox, box in zip(self.bboxes, self.controller.current_boxes()):
            box = self.relative_to_canvas_coords(box)
            bbox.update(box)
        self.canvas.tag_raise("bbox")
        self.canvas.tag_raise("handle")

    def _on_mouse_wheel(self, event):
        self.image_content.on_mouse_wheel(event.x, event.y, event.delta)
        self._update_bounding_boxes()

    def _on_configure(self, _):
        available_width = self.master.winfo_width() - 400
        available_height = self.master.winfo_height() - 50
        if available_width != self.available_width or available_height != self.available_height:
            self.available_height = available_height
            self.available_width = available_width
            self.new_image()
            self._update_bounding_boxes()

    def _on_mouse_click(self, event):
        for bbox in self.bboxes:
            handle = bbox.get_handle_at(event.x, event.y)
            if handle:
                bbox.start_resize(event, handle)
                self.state = self.EventState.RESIZING
                return

        self.state = self.EventState.DRAWING
        self.bboxes.append(
            BoundingBox(
                self.canvas,
                (event.x, event.y, event.x, event.y),
                self.controller.classes_store().get_default_class()["name"],
                self.controller.classes_store(),
                lambda: None,
                len(self.bboxes),
            )
        )
        self.controller.add_box(self.canvas_to_relative_coords(self.bboxes[-1].get_box()), redraw=False)
        self.bboxes[-1].start_resize(event, "se")

    def _on_mouse_drag(self, event):
        if self.state == self.EventState.RESIZING:
            for bbox in self.bboxes:
                bbox.resize(event.x, event.y)
        elif self.state == self.EventState.DRAWING:
            self.bboxes[-1].resize(event.x, event.y)

    def _on_mouse_release(self, event):
        if self.state == self.EventState.RESIZING:
            for bbox in self.bboxes:
                bbox.end_resize()
        elif self.state == self.EventState.DRAWING:
            on_resize_end_callback = lambda: self.controller.change_box(  # noqa: E731
                len(self.bboxes) - 1, self.canvas_to_relative_coords(self.bboxes[-1].get_box()), redraw=False
            )
            self.bboxes[-1].on_resize_end_callback = on_resize_end_callback
            self.bboxes[-1].end_resize()
        self.state = self.EventState.IDLE
