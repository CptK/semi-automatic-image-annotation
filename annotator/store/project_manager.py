import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Literal

from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage


class ProjectManager:
    """Manages saving and loading of annotation projects."""

    def save_project(
        self,
        project_path: str | Path,
        image_store: ImageStore,
        class_store: ClassesStore,
        project_name: str,
        image_handling: Literal["copy", "reference"] = "reference",
        description: str = "",
    ) -> None:
        """Save the current project state to disk.
        
        Args:
            project_path: Path where project should be saved
            image_store: The current ImageStore instance
            class_store: The current ClassesStore instance
            project_name: Name of the project
            image_handling: Whether to copy images or just reference them
            description: Optional project description
        """
        project_path = Path(project_path)
        path_exists = project_path.exists()

        # Create project directory
        if not path_exists:
            project_path.mkdir(parents=True)
            (project_path / "images").mkdir(exist_ok=True)

        # Load or create config
        if path_exists:
            with open(project_path / "config.json") as f:
                config = json.load(f)
            config["last_modified"] = datetime.now().isoformat()
            config["stats"]["total_images"] = len(image_store)
            config["stats"]["annotated_images"] = sum(1 for img in image_store if img.ready)
        else:
            config = {
                "project_name": project_name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "image_handling": image_handling,
                "stats": {
                    "total_images": len(image_store),
                    "annotated_images": sum(1 for img in image_store if img.ready),
                }
            }

        # Handle class definitions
        classes_config = {
            "classes": list(class_store),
            "default_class_uid": class_store.get_default_uid()
        }

        # Handle image data and files
        image_data = []
        existing_images = set()
        
        # If project exists, load existing image data first
        if path_exists and (project_path / "annotations.json").exists():
            with open(project_path / "annotations.json") as f:
                existing_data = json.load(f)
                existing_images = {img_data["path"] for img_data in existing_data}

        for img in image_store:
            if image_handling == "copy":
                # Determine destination path
                dest_path = project_path / "images" / Path(img.path).name
                rel_path = os.path.relpath(dest_path, project_path)
                
                # Only copy if file doesn't exist or path not in existing data
                if not dest_path.exists() or rel_path not in existing_images:
                    shutil.copy2(img.path, dest_path)
            else:
                rel_path = str(img.path)

            # Store image data
            image_data.append({
                "uuid": str(img.uuid),
                "path": rel_path,
                "name": img.name,
                "boxes": img.boxes,
                "label_uids": img.label_uids,
                "ready": img.ready,
                "auto_initialized": img.auto_intialized
            })

        # Save all configurations
        with open(project_path / "config.json", "w") as f:
            json.dump(config, f, indent=4)
            
        with open(project_path / "classes.json", "w") as f:
            json.dump(classes_config, f, indent=4)
            
        with open(project_path / "annotations.json", "w") as f:
            json.dump(image_data, f, indent=4)

    def load_project(
        self,
        project_path: str | Path,
    ) -> tuple['ImageStore', 'ClassesStore']:
        """Load a project from disk.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            A tuple containing (ImageStore, ClassesStore) initialized from the project
        
        Raises:
            FileNotFoundError: If project files are missing
            ValueError: If project files are invalid
        """
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory not found: {project_path}")
            
        required_files = ["config.json", "classes.json", "annotations.json"]
        missing_files = [f for f in required_files if not (project_path / f).exists()]
        if missing_files:
            raise FileNotFoundError(f"Missing project files: {', '.join(missing_files)}")
        
        try:
            # Load configurations
            with open(project_path / "config.json") as f:
                config = json.load(f)
                
            with open(project_path / "classes.json") as f:
                classes_config = json.load(f)
                
            with open(project_path / "annotations.json") as f:
                image_data = json.load(f)

            # Reconstruct class store
            class_store = ClassesStore(classes_config["classes"])
            class_store.set_default_uid(classes_config["default_class_uid"])
            
            # Reconstruct images
            images = []
            for img_info in image_data:
                # Handle relative vs absolute paths
                if config["image_handling"] == "copy":
                    img_path = project_path / img_info["path"]
                else:
                    img_path = img_info["path"]
                    
                if not Path(img_path).exists():
                    print(f"Warning: Image not found: {img_path}")
                    continue

                # Create SingleImage instance
                img = SingleImage(str(img_path), img_info["name"], class_store)
                img.boxes = img_info["boxes"]
                img.label_uids = img_info["label_uids"]
                img.ready = img_info["ready"]
                img.auto_intialized = img_info["auto_initialized"]
                
                images.append(img)
            
            # Create and return stores
            image_store = ImageStore(class_store, None, images)
            return image_store, class_store
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid project file format: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required data in project files: {e}")
