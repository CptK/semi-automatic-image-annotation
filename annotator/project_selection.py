import json
import math
import os
from collections.abc import Callable
from typing import Any

import customtkinter as ctk
from ultralytics import YOLO

from annotator.controller import Controller
from annotator.model.yolo_detection_model import YOLODetectionModel
from annotator.new_project_window import NewProjectWindow
from annotator.store.project_manager import load_project, save_project


class ProjectSelector(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, on_project_selected: Callable, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.on_project_selected = on_project_selected

        self.project_config_file = "project_config.json"
        if not os.path.exists(self.project_config_file):
            with open(self.project_config_file, "w") as f:
                f.write("[]")

        # Constants for sizing
        self.CARD_SIZE = 180  # Size of each card (width and height)
        self.CARD_SPACING = 20  # Spacing between cards

        # Configure the main frame
        self.configure(fg_color="#1e1e1e")

        # Wait for the window to be ready
        self.update_idletasks()

        # Create and configure the title label
        self.title_label = ctk.CTkLabel(self, text="Projects", font=("Arial Bold", 28), text_color="#ffffff")
        self.title_label.pack(pady=(20, 30), padx=20, anchor="w")

        # Create scrollable container for the grid
        self.grid_container = ctk.CTkScrollableFrame(
            self,
            fg_color="#1e1e1e",
        )
        self.grid_container.pack(fill="both", expand=True, padx=20)

        # Wait for container to be ready
        self.update_idletasks()

        # Display initial projects
        self.after(100, lambda: self.display_projects(self.load_recent_projects()))

        # Add resize handler with delay
        self._resize_after_id = None
        self.master.bind("<Configure>", self.on_resize)

    def unbind_resize(self):
        """Unbind resize event"""
        self.master.unbind("<Configure>")

    def create_project_card(
        self, parent: ctk.CTkFrame, project_data: dict[str, str] | None = None, is_new_button: bool = False
    ) -> ctk.CTkFrame:
        """Create a card for either a project or the new project button"""
        # Create main frame with fixed size
        frame = ctk.CTkFrame(
            parent, fg_color="#2a2a2a", width=self.CARD_SIZE, height=self.CARD_SIZE, corner_radius=8
        )
        frame.grid_propagate(False)  # Prevent size changes

        # Create content (plus sign or empty space)
        content = ctk.CTkLabel(
            frame,
            text="+" if is_new_button else "",
            font=("Arial Bold", 48) if is_new_button else None,
            text_color="#00b4d8" if is_new_button else "#ffffff",
            fg_color="#1a1a1a",
            corner_radius=4,
            width=self.CARD_SIZE - 20,
            height=self.CARD_SIZE - 60,
        )
        content.place(relx=0.5, rely=0.4, anchor="center")

        # Add text label
        text = "New Project" if is_new_button else project_data["project_name"]
        text_label = ctk.CTkLabel(frame, text=text, font=("Arial", 13), text_color="#ffffff")
        text_label.place(relx=0.5, rely=0.85, anchor="center")

        # Store command
        command = self.new_project if is_new_button else lambda p=project_data: self.open_project(p)

        # Bind events
        def on_enter(e):
            frame.configure(fg_color="#3a3a3a")

        def on_leave(e):
            frame.configure(fg_color="#2a2a2a")

        for widget in [frame, content, text_label]:
            widget.bind("<Button-1>", lambda e, c=command: c())
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        return frame

    def calculate_grid_dimensions(self, container_width: int) -> tuple[int, int]:
        """Calculate the number of rows and columns based on container width"""
        # Calculate how many cards can fit in a row
        total_card_width = self.CARD_SIZE + self.CARD_SPACING
        num_columns = max(1, (container_width - self.CARD_SPACING) // total_card_width)

        # Calculate number of rows needed
        total_items = len(self.load_recent_projects()) + 1  # +1 for new project button
        num_rows = math.ceil(total_items / num_columns)

        return num_rows, num_columns

    def on_destroy(self, event=None):
        """Handle widget destruction"""
        if event.widget == self:
            self._is_destroyed = True
            if hasattr(self, "_resize_after_id") and self._resize_after_id:
                self.after_cancel(self._resize_after_id)
            self.master.unbind("<Configure>")

    def on_resize(self, event) -> None:
        """Handle window resize events"""
        if event.widget != self.master:  # Only respond to main window resize
            return

        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)

        # Schedule layout update with delay to prevent too frequent updates
        self._resize_after_id = self.after(10, lambda: self.display_projects(self.load_recent_projects()))

    def display_projects(self, projects: list[dict[str, str]]) -> None:
        """Display projects in a grid layout"""
        # Clear existing widgets
        for widget in self.grid_container.winfo_children():
            widget.destroy()

        # Get the master window width
        master_width = self.winfo_toplevel().winfo_width()
        # Account for main frame padding and scrollbar
        container_width = master_width - 100  # 40px for padx=20 on each side + 20px for scrollbar

        num_rows, num_cols = self.calculate_grid_dimensions(container_width)

        # Configure grid columns with equal spacing but no weight
        for i in range(num_cols):
            self.grid_container.grid_columnconfigure(i, weight=0)

        # Create and arrange all cards
        all_items = [{"is_new": True}] + projects

        for idx, item in enumerate(all_items):
            row = idx // num_cols
            col = idx % num_cols

            if item.get("is_new"):
                card = self.create_project_card(self.grid_container, is_new_button=True)
            else:
                card = self.create_project_card(self.grid_container, item)

            # Calculate x position to center cards
            total_width = (num_cols * self.CARD_SIZE) + ((num_cols - 1) * self.CARD_SPACING)
            remaining_space = container_width - total_width
            extra_padding = remaining_space // 2 if remaining_space > 0 else 0

            # Place card in grid without stretching
            card.grid(
                row=row,
                column=col,
                padx=(self.CARD_SPACING // 2 + (extra_padding if col == 0 else 0), self.CARD_SPACING // 2),
                pady=self.CARD_SPACING // 2,
                sticky="",  # No sticky parameter means no stretching
            )

    def load_recent_projects(self) -> list[dict[str, str]]:
        """Load recent projects data"""
        with open(self.project_config_file) as f:
            return json.load(f)

    def new_project(self) -> None:
        """Handle new project creation by opening the new project window."""

        def handle_project_creation(project_data: dict[str, Any], controller: Controller) -> None:
            """Handle the creation of a new project from the project data."""
            save_project(
                project_path=project_data["project_path"],
                image_store=project_data["image_store"],
                class_store=project_data["class_store"],
                project_name=project_data["project_name"],
                description=project_data["description"],
            )

            controller.initialize_project(project_data)

            # Save the project data to the recent projects list
            recent_projects = self.load_recent_projects()
            recent_projects.append(
                {"project_name": project_data["project_name"], "project_path": project_data["project_path"]}
            )
            with open(self.project_config_file, "w") as f:
                json.dump(recent_projects, f, indent=4)

            # After creating the project, refresh the project list
            self.display_projects(self.load_recent_projects())
            self.open_project(project_data)

        # Create a new controller instance for the new project
        yolo_model = YOLO("yolov8m.pt")  # Load the YOLO model
        model = YOLODetectionModel(yolo_model, ["none", "buoy", "boat"])  # Create a detection model
        controller = Controller(["none"], model, [])

        # Open the new project window
        NewProjectWindow(self, controller, handle_project_creation)

    def open_project(self, project: dict[str, str]) -> None:
        """Handle opening an existing project"""
        project_path = project["project_path"]
        config = load_project(project_path)
        controller = Controller(
            classes=config["class_store"],
            detection_model=config["detection_model"],
            initial_images=config["image_store"],
        )
        controller.initialize_project(config)

        # set the selected project to the first project in the list
        recent_projects = self.load_recent_projects()
        recent_projects.insert(0, recent_projects.pop(recent_projects.index(project)))
        with open(self.project_config_file, "w") as f:
            json.dump(recent_projects, f, indent=4)

        self.on_project_selected(controller)
