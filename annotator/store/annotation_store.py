"""This module provides a class for storing and managing annotations."""

import json
import os
from typing import Literal, cast

import yaml
from PIL import Image

from annotator.model.yolo_detection_model import YOLODetectionModel
from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage


class AnnotationStore:
    """A class for storing and managing annotations.

    Args:
        img_paths: A list of paths to the image files.
        model: The object detection model to use for automatic annotation.
        available_labels: A list of available class labels.
    """

    def __init__(self, img_paths: list[str], model, available_labels: list[str]):
        self.class_store = ClassesStore(available_labels)
        self.detection_model = YOLODetectionModel(model, available_labels)
        self.image_store = ImageStore(
            self.class_store, self.detection_model, cast(list[SingleImage | str], img_paths)
        )

    def save(self, path: str):
        """Save the annotations to a JSON file."""
        self.export(path, "json", False, 0.0)

    def import_json(self, path: str, append: bool = False):
        """Import annotations from a JSON file.

        Args:
            path: The path to the input JSON file.
            append: If True, append the annotations to the existing dataset.
        """
        if not path.endswith(".json"):
            raise ValueError("Import path must be a JSON file.")

        with open(path) as f:
            data = json.load(f)

        new_annotations = [SingleImage(a["file_path"], a["file_name"], self.class_store) for a in data]

        if append:
            self.image_store.add_images(cast(list[SingleImage | str], new_annotations))
        else:
            self.image_store = ImageStore(
                self.class_store, self.detection_model, cast(list[SingleImage | str], new_annotations)
            )
