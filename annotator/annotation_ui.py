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
        controller: The controller object for the application.

    Example:
        >>> from annotator.annotation_store import AnnotationStore
        >>> from annotator.annotation_ui import ImageAnnotationGUI
        >>> from annotator.controller import Controller
        >>> from yolo import YOLO
        >>> model = YOLO("yolov8m.pt")
        >>> store = AnnotationStore("path/to/data", model, available_labels=["label1", "label2"])
        >>> controller = Controller(store)
        >>> app = ImageAnnotationGUI(controller)
        >>> controller.set_view(app)
        >>> app.mainloop()
    """

    INITIAL_WIDTH = 1200
    INITIAL_HEIGHT = 800

    HEADER_BAR_HEIGHT = 50
    SIDEBAR_WIDTH = 200

    def __init__(self, controller: Controller) -> None:
        super().__init__()
        self.title("YOLO Image Annotation Tool")
        self.geometry(f"{self.INITIAL_WIDTH}x{self.INITIAL_HEIGHT}")

        self.controller = controller

        self.setup_gui()

    def setup_gui(self) -> None:
        """Set up the GUI layout."""
        self.header = HeaderBar(self, self.controller, height=self.HEADER_BAR_HEIGHT)
        self.header.pack(fill="x", ipadx=10, ipady=10, side="top")

        self.left_sidebar = LeftSidebar(self, self.controller, width=self.SIDEBAR_WIDTH)
        self.left_sidebar.pack(fill="y", side="left")

        self.right_sidebar = RightSidebar(self, self.controller, width=self.SIDEBAR_WIDTH)
        self.right_sidebar.pack(fill="y", side="right")

        self.content = Content(
            self,
            self.controller,
            (self.INITIAL_WIDTH - 2 * self.SIDEBAR_WIDTH, self.INITIAL_HEIGHT - self.HEADER_BAR_HEIGHT),
        )
        self.content.pack()

    def refresh_all(self) -> None:
        """Refresh all GUI elements."""
        self.left_sidebar.update()
        self.right_sidebar.update()
        self.content.new_image()
        self.content.update()

    def redraw_content(self, only_boxes: bool = False) -> None:
        """Redraw the content area."""
        self.content.update(only_boxes)

    def refresh_left_sidebar(self) -> None:
        """Refresh the left sidebar."""
        self.left_sidebar.update()

    def refresh_right_sidebar(self) -> None:
        """Refresh the right sidebar."""
        self.right_sidebar.update()
