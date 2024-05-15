"""This module contains the main GUI class for the image annotation tool."""

import customtkinter as ctk

from annotator.annotation_store import AnnotationStore
from annotator.content import Content
from annotator.header_bar import HeaderBar
from annotator.sidebar_left import LeftSidebar
from annotator.sidebar_right import RightSidebar

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class ImageAnnotationGUI(ctk.CTk):
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
    def __init__(self, annotation_store: AnnotationStore):
        super().__init__()
        self.title("YOLO Image Annotation Tool")
        self.geometry("1200x800")

        self.annotation_store = annotation_store

        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI layout."""
        self.header = HeaderBar(self, self.annotation_store.export)
        self.header.pack(fill="x", ipadx=10, ipady=10, side="top")

        self.left_sidebar = LeftSidebar(self, self.annotation_store, width=200)
        self.left_sidebar.pack(fill="y", side="left")

        self.right_sidebar = RightSidebar(self, self.annotation_store, width=200)
        self.right_sidebar.pack(fill="y", side="right")

        self.content = Content(self, self.annotation_store, width=640, height=640)
        self.content.pack()

        self.left_sidebar.update()
        self.right_sidebar.update()
        self.content.update()

    def jump_to_image(self, idx):
        """Jump to a specific image index.
        
        Args:
            idx: The index of the image to jump to.
        """
        self.annotation_store.jump_to(idx)
        self.content.update()
        self.left_sidebar.update()
        self.right_sidebar.update()

    def next_image(self):
        """Move to the next image in the sequence."""
        self.annotation_store.next()
        self.content.update()
        self.left_sidebar.update()
        self.right_sidebar.update()

    def redraw_content(self):
        """Redraw the content area."""
        self.content.update()
