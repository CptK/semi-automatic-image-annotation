import json
from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

class ProjectSelectionDialog(ctk.CTkToplevel):
    """Initial dialog for selecting between creating a new project or opening an existing one."""
    
    def __init__(self, parent, callback: Callable[[dict], None], **kwargs):
        super().__init__(parent, **kwargs)
        self.title("Project Selection")
        self.callback = callback
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.geometry("400x500")
        self.resizable(False, False)
        
        self._create_widgets()
        self._load_recent_projects()

    def _create_widgets(self):
        # Title
        title = ctk.CTkLabel(self, text="Select Project", font=("Helvetica", 20))
        title.pack(pady=20)
        
        # New Project Button
        new_project_btn = ctk.CTkButton(
            self, 
            text="Create New Project", 
            command=self._create_new_project,
            height=40
        )
        new_project_btn.pack(pady=10, padx=20, fill="x")
        
        # Open Project Button
        open_project_btn = ctk.CTkButton(
            self, 
            text="Open Existing Project", 
            command=self._open_project,
            height=40
        )
        open_project_btn.pack(pady=10, padx=20, fill="x")
        
        # Recent Projects Section
        recent_label = ctk.CTkLabel(self, text="Recent Projects", font=("Helvetica", 16))
        recent_label.pack(pady=(20, 10))
        
        self.recent_frame = ctk.CTkScrollableFrame(self, height=200)
        self.recent_frame.pack(pady=10, padx=20, fill="x")

    def _load_recent_projects(self):
        # TODO: Load from a config file
        recent_projects = []
        if (Path.home() / ".image_annotator" / "recent_projects.json").exists():
            with open(Path.home() / ".image_annotator" / "recent_projects.json") as f:
                recent_projects = json.load(f)
        
        for project in recent_projects:
            self._add_recent_project_button(project)

    def _add_recent_project_button(self, project_info: dict):
        btn = ctk.CTkButton(
            self.recent_frame,
            text=f"{project_info['name']} ({project_info['path']})",
            command=lambda: self._open_recent_project(project_info),
        )
        btn.pack(pady=5, fill="x")

    def _create_new_project(self):
        self.withdraw()
        ProjectCreationDialog(self, self.callback)

    def _open_project(self):
        path = filedialog.askdirectory(title="Select Project Directory")
        if path:
            self.callback({"action": "open", "path": path})
            self.destroy()

    def _open_recent_project(self, project_info: dict):
        self.callback({"action": "open", "path": project_info["path"]})
        self.destroy()


class ClassDefinitionFrame(ctk.CTkFrame):
    """Frame for defining classes during project creation."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.class_entries = []
        self._create_widgets()

    def _create_widgets(self):
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(header, text="Class Name").pack(side="left", expand=True)
        ctk.CTkLabel(header, text="Color").pack(side="left", padx=10)
        ctk.CTkLabel(header, text="Default").pack(side="left", padx=10)
        ctk.CTkLabel(header, text="").pack(side="left", width=30)  # Spacing for delete button
        
        self.classes_frame = ctk.CTkScrollableFrame(self, height=200)
        self.classes_frame.pack(fill="x", expand=True, padx=5)
        
        # Add initial class
        self._add_class()
        
        # Add button
        add_btn = ctk.CTkButton(self, text="Add Class", command=self._add_class)
        add_btn.pack(pady=10)

    def _add_class(self):
        frame = ctk.CTkFrame(self.classes_frame)
        frame.pack(fill="x", pady=2)
        
        name = ctk.CTkEntry(frame)
        name.pack(side="left", expand=True)
        
        color = ctk.CTkButton(
            frame, 
            text="", 
            width=30,
            command=lambda: self._choose_color(color)
        )
        color.configure(fg_color="red")  # Default color
        color.pack(side="left", padx=10)
        
        is_default = ctk.CTkCheckBox(frame, text="")
        is_default.pack(side="left", padx=10)
        
        delete_btn = ctk.CTkButton(
            frame, 
            text="X", 
            width=30,
            command=lambda: self._delete_class(frame)
        )
        delete_btn.pack(side="left", padx=5)
        
        self.class_entries.append((frame, name, color, is_default))

    def _choose_color(self, button):
        color = ctk.CTkColorChooser.ask_color()
        if color:
            button.configure(fg_color=color)

    def _delete_class(self, frame):
        if len(self.class_entries) > 1:  # Keep at least one class
            frame.destroy()
            self.class_entries = [(f, n, c, d) for (f, n, c, d) in self.class_entries if f != frame]

    def get_classes(self) -> list[dict]:
        classes = []
        for _, name, color, is_default in self.class_entries:
            if name.get().strip():  # Only include classes with names
                classes.append({
                    "name": name.get().strip(),
                    "color": color.cget("fg_color"),
                    "default": is_default.get()
                })
        return classes


class ProjectCreationDialog(ctk.CTkToplevel):
    """Dialog for creating a new project."""
    
    def __init__(self, parent, callback: Callable[[dict], None], **kwargs):
        super().__init__(parent, **kwargs)
        self.title("Create New Project")
        self.callback = callback
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.geometry("600x800")
        self.resizable(False, False)
        
        self._create_widgets()

    def _create_widgets(self):
        # Project Details
        details_frame = ctk.CTkFrame(self)
        details_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(details_frame, text="Project Name:").pack(anchor="w", pady=5)
        self.name_entry = ctk.CTkEntry(details_frame)
        self.name_entry.pack(fill="x", pady=5)
        
        ctk.CTkLabel(details_frame, text="Project Location:").pack(anchor="w", pady=5)
        
        path_frame = ctk.CTkFrame(details_frame)
        path_frame.pack(fill="x", pady=5)
        
        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.pack(side="left", fill="x", expand=True)
        
        browse_btn = ctk.CTkButton(
            path_frame, 
            text="Browse", 
            command=self._browse_location,
            width=100
        )
        browse_btn.pack(side="right", padx=5)
        
        ctk.CTkLabel(details_frame, text="Description:").pack(anchor="w", pady=5)
        self.description_entry = ctk.CTkTextbox(details_frame, height=100)
        self.description_entry.pack(fill="x", pady=5)
        
        # Image Handling
        image_frame = ctk.CTkFrame(self)
        image_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(image_frame, text="Image Handling:").pack(anchor="w", pady=5)
        self.image_handling = ctk.CTkOptionMenu(
            image_frame,
            values=["Copy images to project", "Reference original images"]
        )
        self.image_handling.pack(fill="x", pady=5)
        
        # Class Definition
        class_frame = ctk.CTkFrame(self)
        class_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(class_frame, text="Define Classes:").pack(anchor="w", pady=5)
        self.class_definition = ClassDefinitionFrame(class_frame)
        self.class_definition.pack(fill="both", expand=True, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Create Project",
            command=self._create_project,
            width=100
        ).pack(side="right", padx=5)

    def _browse_location(self):
        path = filedialog.askdirectory(title="Select Project Location")
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)

    def _cancel(self):
        parent = self.master
        self.destroy()
        parent.deiconify()

    def _create_project(self):
        # Validate inputs
        if not self.name_entry.get().strip():
            # TODO: Show error
            return
            
        if not self.path_entry.get().strip():
            # TODO: Show error
            return
            
        classes = self.class_definition.get_classes()
        if not classes:
            # TODO: Show error
            return
            
        # Prepare project info
        project_info = {
            "action": "create",
            "name": self.name_entry.get().strip(),
            "path": self.path_entry.get().strip(),
            "description": self.description_entry.get("1.0", "end").strip(),
            "image_handling": "copy" if self.image_handling.get() == "Copy images to project" else "reference",
            "classes": classes
        }
        
        self.callback(project_info)
        self.destroy()
