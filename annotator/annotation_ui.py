"""This module contains the main GUI class for the image annotation tool."""

import customtkinter as ctk

from annotator.content import Content
from annotator.controller import Controller
from annotator.header_bar import HeaderBar
from annotator.sidebar_left import LeftSidebar
from annotator.sidebar_right import RightSidebar
from annotator.ui import UI

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class ImageAnnotationGUI(UI):
    """Main GUI class for the image annotation tool.

    Args:
        annotation_store: The annotation store object to use for image data.

    Example:
        >>> from annotator.annotation_store import AnnotationStore
        >>> from annotator.annotation_ui import ImageAnnotationGUI
        >>> from yolo import YOLO
        >>> model = YOLO("yolov8m.pt")
        >>> store = AnnotationStore("path/to/data", model, available_labels=["label1", "label2"])
        >>> gui = ImageAnnotationGUI(store)
        >>> gui.mainloop()
    """

    def __init__(self, controller: Controller):
        super().__init__()
        self.title("YOLO Image Annotation Tool")
        self.geometry("1200x800")

        self.controller = controller

        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI layout."""
        self.header = HeaderBar(self, self.controller.export)
        self.header.pack(fill="x", ipadx=10, ipady=10, side="top")

        self.left_sidebar = LeftSidebar(self, self.controller, width=200)
        self.left_sidebar.pack(fill="y", side="left")

        self.right_sidebar = RightSidebar(self, self.controller, width=200)
        self.right_sidebar.pack(fill="y", side="right")

        self.content = Content(self, self.controller, width=640, height=640)
        self.content.pack()

        self.left_sidebar.update()
        self.right_sidebar.update()
        self.content.update()

    def refresh_all(self):
        """Refresh all GUI elements."""
        self.left_sidebar.update()
        self.right_sidebar.update()
        self.content.new_image()
        self.content.update()

    def redraw_content(self):
        """Redraw the content area."""
        self.content.update()

    def refresh_left_sidebar(self):
        """Refresh the left sidebar."""
        self.left_sidebar.update()

    def refresh_right_sidebar(self):
        """Refresh the right sidebar."""
        self.right_sidebar.update()
