"""Main module for the annotator application."""

import customtkinter as ctk

from annotator.annotation_ui import ImageAnnotationGUI
from annotator.controller import Controller
from annotator.project_selection import ProjectSelector


class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initial window setup
        self.title("YOLO Image Annotation Tool")
        self.configure(fg_color="#1e1e1e")
        self.geometry("800x600")
        self.minsize(800, 600)

        # Initialize current view tracker
        self.current_view = None

        # Show initial view
        self.show_project_selector()

    def show_project_selector(self):
        """Show the project selector screen"""
        # Clean up current view
        self._clear_current_view()

        # Create and pack the project selector
        self.current_view = ProjectSelector(self, on_project_selected=self.show_annotation_gui)
        self.current_view.pack(fill="both", expand=True)

    def show_annotation_gui(self, controller: Controller):
        """Show the annotation GUI"""
        # Clean up current view
        self._clear_current_view()

        # Create and pack the annotation GUI
        self.current_view = ImageAnnotationGUI(self, controller)
        controller.set_view(self.current_view)
        self.current_view.pack(fill="both", expand=True)

        # Update window size for annotation view
        self.geometry(f"{ImageAnnotationGUI.INITIAL_WIDTH}x{ImageAnnotationGUI.INITIAL_HEIGHT}")

    def _clear_current_view(self):
        """Clean up the current view before switching"""
        if self.current_view:
            # Common events to unbind
            events = [
                "<Configure>",  # Window/widget resize
                "<Button-1>",
                "<Button-2>",
                "<Button-3>",  # Mouse clicks
                "<ButtonRelease-1>",
                "<ButtonRelease-2>",
                "<ButtonRelease-3>",
                "<Motion>",  # Mouse movement
                "<Key>",  # Keyboard
                "<Enter>",
                "<Leave>",  # Mouse enter/leave widget
            ]

            # Unbind all common events from both the view and the main window
            for event in events:
                self.current_view.unbind(event)
                self.unbind(event)

        for widget in self.winfo_children():
            widget.destroy()

        self.current_view = None


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
