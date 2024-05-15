"""This module provides a class for storing and managing annotations."""

import json
import os
from typing import Literal
import yaml

from PIL import Image


class AnnotationStore:
    """A class for storing and managing annotations.

    Args:
        data_path: The path to the directory containing the images.
        model: The object detection model to use for automatic annotation.
        available_labels: A list of available class labels.
    """

    def __init__(self, data_path: str, model, available_labels: list[str]):
        img_files = [f for f in os.listdir(data_path)]
        self.model = model
        self.data_path = data_path
        self.available_labels = available_labels

        self.annotations = [
            {"file_name": img, "boxes": [], "labels": [], "marked_ready": False, "auto_intialized": False}
            for img in img_files
        ]

        self.current: int = 0
        self.jump_to(self.current)

    def next(self):
        """Move to the next image in the dataset. If the end of the dataset is reached, do nothing.
        
        If the next image has not been seen before, initialize it with automatic annotation.
        """
        self.current = self.current + 1

        if self.current >= len(self.annotations):
            return

        if not self.annotations[self.current]["auto_intialized"]:
            self.init_image()

    def jump_to(self, index):
        """Jump to a specific image in the dataset.

        If the image has not been seen before, initialize it with automatic annotation.
        
        Args:
            index: The index of the image to jump to.
        """
        self.current = index
        if not self.annotations[self.current]["auto_intialized"]:
            self.init_image()

    def save(self):
        raise NotImplementedError

    def export(self, path: str, format: Literal["csv", "json", "yolo"], only_ready: bool, train_split: float):
        """Export the annotations to a file in the specified format.

        Args:
            path: The path to the output file or directory.
            format: The format in which to export the annotations (csv, json, or yolo).
            only_ready: If True, only export images that have been marked as ready.
            train_split: The fraction of the data to use for training in the YOLO format.
        """
        data = [a for a in self.annotations if not only_ready or a["marked_ready"]]
        if format.lower() == "csv":
            self._export_csv(path, data)
        elif format.lower() == "json":
            self._export_json(path, data)
        elif format.lower() == "yolo":
            train = data[: int(len(data) * train_split)]
            test = data[int(len(data) * train_split) :]
            self._export_yolo(path, train, test)

    def init_image(self):
        """Initialize the current image with automatic annotation using the object detection model."""
        if self.model is not None:
            img = Image.open(self.file_path)
            res = self._detect_single(img)
            self.annotations[self.current]["boxes"] = [r["box"] for r in res]
            self.annotations[self.current]["labels"] = [r["label"] for r in res]
            self.annotations[self.current]["auto_intialized"] = True

    def _detect_single(self, img):
        """Detect objects in a single image and return the results as a list of dictionaries.

        Args:
            img: The image to process.

        Returns:
            A list of dictionaries, each containing the keys 'box' for the bounding box coordinates, 'boxn'
            for the normalized bounding box coordinates, 'label' for the class label, and 'confidence' for the
            detection confidence.
        """
        img = img.resize((640, 640))
        results = self.model(img)[0]
        labels = results.names
        boxes = results.boxes
        res = []
        for box in boxes:
            label = labels[box.cls.item()]
            if label not in self.available_labels:
                label = "none"
            res.append(
                {
                    "box": box.xyxy[0].tolist(),
                    "boxn": box.xyxyn[0].tolist(),
                    "label": label,
                    "confidence": box.conf.item(),
                }
            )
        return res

    def annotation_by_name(self, name):
        """Get the index of the annotation with the specified file name.

        Args:
            name: The file name of the image.

        Returns:
            The index of the annotation with the specified file name, or None if not found.
        """
        for i, a in enumerate(self.annotations):
            if a["file_name"] == name:
                return i
        return None

    def mark_ready(self):
        """Mark the *current* image as ready for export."""
        self.annotations[self.current]["marked_ready"] = True

    def change_label(self, idx, label):
        """Change the label of a bounding box in the *current* image."""
        self.annotations[self.current]["labels"][idx] = label  # type: ignore

    def delete(self, idx):
        """Delete a bounding box from the *current* image."""
        self.annotations[self.current]["boxes"].pop(idx)  # type: ignore
        self.annotations[self.current]["labels"].pop(idx)  # type: ignore

    def add_box(self, box, label="none"):
        """Add a bounding box to the *current* image."""
        self.annotations[self.current]["boxes"].append(box)  # type: ignore
        self.annotations[self.current]["labels"].append(label)  # type: ignore

    @property
    def file_path(self):
        """The absolute file path of the *current* image."""
        return os.path.join(self.data_path, str(self.annotations[self.current]["file_name"]))

    @property
    def boxes(self):
        """The bounding boxes of the *current* image."""
        return self.annotations[self.current]["boxes"]

    @property
    def labels(self):
        """The class labels of the *current* image."""
        return self.annotations[self.current]["labels"]

    @property
    def ready(self):
        """Whether the *current* image has been marked as ready for export."""
        return self.annotations[self.current]["marked_ready"]

    @property
    def image_names(self):
        """A list of file names of all images in the dataset."""
        return [a["file_name"] for a in self.annotations]

    def _export_csv(self, path: str, data: list[dict], delimiter: str = ";"):
        """Export the annotations to a CSV file.

        Args:
            path: The path to the output CSV file.
            data: The list of annotations to export.
            delimiter: The delimiter to use for separating fields in the CSV file.
        """
        if not path.endswith(".csv"):
            raise ValueError("Export path must be a CSV file.")

        with open(path, "w") as f:
            for a in data:
                for box, label in zip(a["boxes"], a["labels"]):
                    x1, y1, x2, y2 = box
                    f.write(
                        f"{a['file_name']}{delimiter}{x1}{delimiter}{y1}{delimiter}{x2}{delimiter}{y2}{delimiter}{label}\n"
                    )

    def _export_json(self, path: str, data: list[dict]):
        """Export the annotations to a JSON file.

        Args:
            path: The path to the output JSON file.
            data: The list of annotations to export.
        """
        if not path.endswith(".json"):
            raise ValueError("Export path must be a JSON file.")

        with open(path, "w") as f:
            json.dump(data, f)

    def _export_yolo(self, path: str, train: list[dict], test: list[dict]):
        """Export the annotations to the YOLO format.

        Args:
            path: The path to the output directory.
            train: The list of annotations to use for training.
            test: The list of annotations to use for testing.
        """
        if not os.path.exists(path):
            os.makedirs(path)

        os.makedirs(os.path.join(path, "train", "images"), exist_ok=True)
        os.makedirs(os.path.join(path, "train", "labels"), exist_ok=True)
        os.makedirs(os.path.join(path, "test", "images"), exist_ok=True)
        os.makedirs(os.path.join(path, "test", "labels"), exist_ok=True)

        for i, data in enumerate(train):
            img = Image.open(os.path.join(self.data_path, data["file_name"]))
            img = img.resize((640, 640))
            img.save(os.path.join(path, "train", "images", f"{i}.jpg"))

            with open(os.path.join(path, "train", "labels", f"{i}.txt"), "w") as f:
                for box, label in zip(data["boxes"], data["labels"]):
                    x1, y1, x2, y2 = box

                    # get the center of the box in range 0-1
                    x_center = (x1 + x2) / (2 * 640)
                    y_center = (y1 + y2) / (2 * 640)
                    width = (x2 - x1) / 640
                    height = (y2 - y1) / 640

                    # write the label and the normalized box coordinates
                    f.write(f"{self.available_labels.index(label)} {x_center} {y_center} {width} {height}\n")

        for i, data in enumerate(test):
            img = Image.open(os.path.join(self.data_path, data["file_name"]))
            img = img.resize((640, 640))
            img.save(os.path.join(path, "test", "images", f"{i}.jpg"))

            with open(os.path.join(path, "test", "labels", f"{i}.txt"), "w") as f:
                for box, label in zip(data["boxes"], data["labels"]):
                    x1, y1, x2, y2 = box

                    # get the center of the box in range 0-1
                    x_center = (x1 + x2) / (2 * 640)
                    y_center = (y1 + y2) / (2 * 640)
                    width = (x2 - x1) / 640
                    height = (y2 - y1) / 640

                    # write the label and the normalized box coordinates
                    f.write(f"{self.available_labels.index(label)} {x_center} {y_center} {width} {height}\n")

        # create a yaml config file
        data_yaml = {
            "train": os.path.join(path, "train").replace("\\", "/"),
            "val": os.path.join(path, "test").replace("\\", "/"),
            "nc": len(self.available_labels),
            "names": {i: label for i, label in enumerate(self.available_labels)},
        }

        with open(os.path.join(path, "data.yaml"), "w") as f:
            yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)
