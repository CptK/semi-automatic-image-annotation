"""Content module for the annotator application."""

from enum import Enum

import customtkinter as ctk
from PIL import Image, ImageTk

from annotator.bounding_box import BoundingBox
from annotator.controller import Controller


class ImageContent(ImageTk.PhotoImage):
    """Image content class for the annotator application. Supports zooming in and out of the image.

    Args:
        image_path: The path to the image file.
        initial_size: The initial size of the image content area.
    """

    def __init__(self, image_path: str, initial_size: tuple[int, int], **kwargs) -> None:
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
        """Calculate the size of the image to fit the available space.

        Args:
            image_size: The size of the image.

        Returns:
            The width and height of the image that fits the available space.
        """
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
        """Configure the image content area with the new available space.

        Args:
            available_width: The available width for the image content area.
            available_height: The available height for the image content area.
        """
        self.available_width = available_width
        self.available_height = available_height
        self.img_width, self.img_height = self.calc_fit_size(self.original_image.size)
        self.image = self.image.resize((self.img_width, self.img_height))
        self.paste(self.image)

    def zoom(self) -> None:
        """Zoom in or out of the image."""
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

    def on_mouse_wheel(self, event_x: int, event_y: int, event_delta) -> None:
        """Handle the mouse wheel event to zoom in or out of the image.

        Args:
            event_x: The x-coordinate of the mouse event.
            event_y: The y-coordinate of the mouse event.
            event_delta: The delta value of the mouse wheel event.
        """
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
        controller: The controller object to use for data manipulation.
        initial_size: The initial size of the content area.
    """

    class EventState(Enum):
        """Enumeration for the event states.

        IDLE: The content area is idle, i.e. nothing is drawn or resized.
        DRAWING: The content area is in drawing mode, i.e., drawing a new bounding box.
        RESIZING: The content area is in resizing mode, i.e., resizing a bounding box.
        """

        IDLE = 0
        DRAWING = 1
        RESIZING = 2

    def __init__(self, master, controller: Controller, initial_size: tuple[int, int], **kwargs) -> None:
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

    def update(self, only_boxes: bool = False) -> None:
        """Update the content area."""
        if not only_boxes:
            self.new_image()
        self._create_bounding_boxes()

    def new_image(self) -> None:
        """Load a new image into the content area."""
        current_img = self.controller.current()

        try:
            if not current_img:
                raise Exception("No image available to load.")

            self.image_content = ImageContent(current_img.path, (self.available_width, self.available_height))
            self.canvas.config(width=self.image_content.img_width, height=self.image_content.img_height)
            self.canvas.create_image(0, 0, anchor="nw", image=self.image_content)
            self.canvas.lower(self.image_content)

        except Exception as e:
            if current_img:
                print(f"Failed to load image {current_img.path}: {e}")
            else:
                print("No image available to load.")
            self.canvas.delete("all")

    def relative_to_canvas_coords(
        self, box: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        """Convert relative bounding box coordinates to canvas coordinates.

        Args:
            box: The relative bounding box coordinates (center_x, center_y, width, height).

        Returns:
            The bounding box coordinates in canvas coordinates (x1, y1, x2, y2).
        """
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

    def canvas_to_relative_coords(
        self, canvas_coords: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        """Convert canvas bounding box coordinates to relative coordinates.

        Args:
            canvas_coords: The bounding box coordinates in canvas coordinates (x1, y1, x2, y2).

        Returns:
            The relative bounding box coordinates (center_x, center_y, width, height).
        """
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

    def _create_bounding_boxes(self) -> None:
        """Create the bounding boxes for the current image."""
        self.canvas.delete("bbox")
        self.canvas.delete("handle")
        self.bboxes = []
        current_img = self.controller.current()

        if not current_img:
            return

        for i, (box, label_uid) in enumerate(zip(current_img.boxes, current_img.label_uids)):
            box = self.relative_to_canvas_coords(box)
            on_resize_end_callback = lambda idx=i: self.controller.change_image_annotation(  # noqa: E731
                idx, self.canvas_to_relative_coords(self.bboxes[idx].get_box()), None, redraw=False
            )
            bbox = BoundingBox(self.canvas, box, label_uid, self.controller, on_resize_end_callback, i)
            self.bboxes.append(bbox)

    def _update_bounding_boxes(self) -> None:
        """Update the bounding boxes for the current image."""
        current_img = self.controller.current()
        if not current_img:
            return

        for bbox, box in zip(self.bboxes, current_img.boxes):
            box = self.relative_to_canvas_coords(box)
            bbox.update(box)
        self.canvas.tag_raise("bbox")
        self.canvas.tag_raise("handle")

    def _on_mouse_wheel(self, event) -> None:
        """Handle the mouse wheel event."""
        self.image_content.on_mouse_wheel(event.x, event.y, event.delta)
        self._update_bounding_boxes()

    def _on_configure(self, _) -> None:
        """Handle the configure event."""
        available_width = self.master.winfo_width() - 400
        available_height = self.master.winfo_height() - 50
        if available_width != self.available_width or available_height != self.available_height:
            self.available_height = available_height
            self.available_width = available_width
            self.new_image()
            self._update_bounding_boxes()

    def _on_mouse_click(self, event) -> None:
        """Handle the mouse click event."""
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
                self.controller.get_default_class_uid(),
                self.controller,
                lambda: None,
                len(self.bboxes),
            )
        )
        coords = self.canvas_to_relative_coords(self.bboxes[-1].get_box())
        self.controller.add_box(coords, self.bboxes[-1].class_uid, redraw=False)
        self.bboxes[-1].start_resize(event, "se")

    def _on_mouse_drag(self, event) -> None:
        """Handle the mouse drag event."""
        if self.state == self.EventState.RESIZING:
            for bbox in self.bboxes:
                bbox.resize(event.x, event.y)
        elif self.state == self.EventState.DRAWING:
            self.bboxes[-1].resize(event.x, event.y)

    def _on_mouse_release(self, event) -> None:
        """Handle the mouse release event."""
        if self.state == self.EventState.RESIZING:
            for bbox in self.bboxes:
                bbox.end_resize()
        elif self.state == self.EventState.DRAWING:
            on_resize_end_callback = lambda: self.controller.change_image_annotation(  # noqa: E731
                len(self.bboxes) - 1,
                self.canvas_to_relative_coords(self.bboxes[-1].get_box()),
                None,
                redraw=False,
            )
            self.bboxes[-1].on_resize_end_callback = on_resize_end_callback
            self.bboxes[-1].end_resize()
        self.state = self.EventState.IDLE
