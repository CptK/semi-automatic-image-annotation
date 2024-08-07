"""Bounding box class for drawing and resizing bounding boxes on a canvas."""

from collections.abc import Callable
from tkinter import TclError

import customtkinter as ctk

from annotator.controller import Controller

RESIZE_CURSORS = {
    "nw": "top_left_corner",
    "ne": "top_right_corner",
    "sw": "bottom_left_corner",
    "se": "bottom_right_corner",
    "n": "top_side",
    "s": "bottom_side",
    "w": "left_side",
    "e": "right_side",
}


class BoundingBox:
    """ "Bounding box class for drawing and resizing bounding boxes on a canvas.

    Args:
        canvas: The canvas to draw the bounding box on.
        box: The coordinates of the bounding box (x1, y1, x2, y2).
        class_uid: The class UID of the object class.
        controller: The controller object.
        on_resize_end_callback: The callback function to call when resizing ends.
        id: The ID of the bounding box.
        label_color: The color of the label text.
        label_font_size: The font size of the label text.
        label_font: The font of the label text.
        handle_size: The size of the resize handles.
    """

    LABEL_OFFSET = 18

    def __init__(
        self,
        canvas: ctk.CTkCanvas,
        box: tuple[int, int, int, int],
        class_uid: int,
        controller: Controller,
        on_resize_end_callback: Callable | None = None,
        id: int | None = None,
        label_color: str = "black",
        label_font_size: int = 12,
        label_font: str = "Helvetica",
        handle_size: int = 6,
    ) -> None:
        self.canvas = canvas
        self.box = box
        self.x1, self.y1, self.x2, self.y2 = box
        self.class_uid = class_uid
        self.controller = controller
        self.id = id
        self.on_resize_end_callback = on_resize_end_callback
        self.label_color = label_color
        self.label_font_size = label_font_size
        self.label_font = label_font
        self.handle_size = handle_size
        self.handles: dict[str, int] = {}
        self.resizing = False

        self.draw()
        self._create_handles()

    def draw(self):
        """Draw the bounding box on the canvas."""
        self.rect = self.canvas.create_rectangle(
            *self.box, outline=self.controller.get_class_color(self.class_uid), tags="bbox"
        )
        text = f"{self.id}: {self.label}" if self.id is not None else f"{self.label}"
        self.label_id = self.canvas.create_text(
            self.box[0],
            self.box[1] - self.LABEL_OFFSET,
            text=text,
            anchor="nw",
            fill=self.label_color,
            font=(self.label_font, self.label_font_size),
            tags="bbox",
        )
        # create a filled rectangle behind the label
        self.label_bg = self.canvas.create_rectangle(
            *self.canvas.bbox(self.label_id),
            fill=self.controller.get_class_color(self.class_uid),
            outline=self.controller.get_class_color(self.class_uid),
            tags="bbox",
        )
        self.canvas.tag_lower(self.label_bg, self.label_id)

    def get_handle_at(self, x: int, y: int) -> str | None:
        """Check if a handle is at the given coordinates."""
        for pos, handle in self.handles.items():
            bbox = self.canvas.bbox(handle)
            if bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
                return pos
        return None

    def _create_handles(self):
        """Create the resize handles for the bounding box."""
        center_positions = {
            "nw": (self.x1, self.y1),
            "ne": (self.x2, self.y1),
            "sw": (self.x1, self.y2),
            "se": (self.x2, self.y2),
            "n": ((self.x1 + self.x2) / 2, self.y1),
            "e": (self.x2, (self.y1 + self.y2) / 2),
            "s": ((self.x1 + self.x2) / 2, self.y2),
            "w": (self.x1, (self.y1 + self.y2) / 2),
        }

        for pos, (x, y) in center_positions.items():
            handle = self.canvas.create_rectangle(
                x - self.handle_size / 2,
                y - self.handle_size / 2,
                x + self.handle_size / 2,
                y + self.handle_size / 2,
                outline=self.controller.get_class_color(self.class_uid),
                fill=self.controller.get_class_color(self.class_uid),
                tags="handle",
            )
            self.handles[pos] = handle

            self.canvas.tag_bind(handle, "<Enter>", lambda event, pos=pos: self._change_cursor(event, pos))
            self.canvas.tag_bind(handle, "<Leave>", lambda event: self._reset_cursor(event))

    def _update_handles(self):
        """Update handle positions after resizing."""
        positions = {
            "nw": (self.x1, self.y1),
            "ne": (self.x2, self.y1),
            "sw": (self.x1, self.y2),
            "se": (self.x2, self.y2),
            "n": ((self.x1 + self.x2) / 2, self.y1),
            "s": ((self.x1 + self.x2) / 2, self.y2),
            "w": (self.x1, (self.y1 + self.y2) / 2),
            "e": (self.x2, (self.y1 + self.y2) / 2),
        }

        for pos, (x, y) in positions.items():
            self.canvas.coords(
                self.handles[pos],
                x - self.handle_size / 2,
                y - self.handle_size / 2,
                x + self.handle_size / 2,
                y + self.handle_size / 2,
            )

        # update the color of the handles, the bounding box and the label
        self.canvas.itemconfig(self.rect, outline=self.controller.get_class_color(self.class_uid))
        self.canvas.itemconfig(self.label_id, fill=self.label_color)
        self.canvas.itemconfig(
            self.label_bg,
            fill=self.controller.get_class_color(self.class_uid),
            outline=self.controller.get_class_color(self.class_uid),
        )
        for handle in self.handles.values():
            self.canvas.itemconfig(
                handle,
                outline=self.controller.get_class_color(self.class_uid),
                fill=self.controller.get_class_color(self.class_uid),
            )

    def update(self, box):
        """Update the bounding box with new coordinates."""
        self.box = box
        self.x1, self.y1, self.x2, self.y2 = box
        self.canvas.coords(self.rect, *self.box)
        self.canvas.coords(self.label_id, self.box[0], self.box[1] - self.LABEL_OFFSET)

        # update the label text
        text = f"{self.id}: {self.label}" if self.id is not None else f"{self.label}"
        self.canvas.itemconfig(self.label_id, text=text)

        self.canvas.coords(self.label_bg, *self.canvas.bbox(self.label_id))
        self._update_handles()

    def _change_cursor(self, event, pos):
        """Change the cursor when hovering over a resize handle."""
        try:
            self.canvas.config(cursor=RESIZE_CURSORS[pos])
        except TclError:
            self.canvas.config(cursor="")

    def _reset_cursor(self, event):
        """Reset the cursor when leaving a resize handle."""
        self.canvas.config(cursor="")

    def start_resize(self, event, pos):
        """Start resizing the bounding box."""
        self.canvas.config(cursor=RESIZE_CURSORS[pos])
        self.active_handle = pos
        self.start_x = event.x
        self.start_y = event.y
        self.resizing = True

    def resize(self, x, y):
        """Resize the bounding box.

        Args:
            x: The x-coordinate of the mouse on the canvas.
            y: The y-coordinate of the mouse on the canvas.
        """
        if not self.resizing:
            return

        if self.active_handle == "nw":
            self.x1 = x
            self.y1 = y
        elif self.active_handle == "ne":
            self.x2 = x
            self.y1 = y
        elif self.active_handle == "sw":
            self.x1 = x
            self.y2 = y
        elif self.active_handle == "se":
            self.x2 = x
            self.y2 = y
        elif self.active_handle == "n":
            self.y1 = y
        elif self.active_handle == "e":
            self.x2 = x
        elif self.active_handle == "s":
            self.y2 = y
        elif self.active_handle == "w":
            self.x1 = x

        self.box = (self.x1, self.y1, self.x2, self.y2)
        self.update(self.box)

    def end_resize(self):
        """End resizing the bounding box."""
        if hasattr(self, "active_handle"):
            del self.active_handle
        if not self.resizing:
            return
        self.resizing = False
        self.canvas.config(cursor="")
        if self.on_resize_end_callback is not None:
            self.on_resize_end_callback()

    def get_box(self) -> tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2

    @property
    def label(self):
        return self.controller.get_class_name(self.class_uid)
