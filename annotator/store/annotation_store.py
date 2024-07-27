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

    def export(self, path: str, format: Literal["csv", "json", "yolo"], only_ready: bool, train_split: float):
        """Export the annotations to a file in the specified format.

        Args:
            path: The path to the output file or directory.
            format: The format in which to export the annotations (csv, json, or yolo).
            only_ready: If True, only export images that have been marked as ready.
            train_split: The fraction of the data to use for training in the YOLO format.
        """
        data = [a for a in self.image_store if not only_ready or a.ready]
        if format.lower() == "csv":
            self._export_csv(path, data)
        elif format.lower() == "json":
            self._export_json(path)
        elif format.lower() == "yolo":
            train = data[: int(len(data) * train_split)]
            test = data[int(len(data) * train_split) :]
            self._export_yolo(path, train, test)

    def change_label(self, idx, label_uid: int):
        """Change the label of a bounding box in the *current* image."""
        self.current.change_label(idx, label_uid)

    def add_box(self, box, label_uid: int | None = None):
        """Add a bounding box to the *current* image."""
        if label_uid is None:
            label_uid = self.class_store.get_default_uid()
        self.current.add_box(box, label_uid)

    def change_box(self, idx, box):
        """Change the coordinates of a bounding box in the *current* image."""
        self.current.boxes[idx] = box

    @property
    def current(self) -> SingleImage:
        """The index of the *current* image in the dataset."""
        return self.image_store.active_image

    @property
    def file_path(self):
        """The absolute file path of the *current* image."""
        return self.current.path

    @property
    def boxes(self):
        """The bounding boxes of the *current* image."""
        return self.current.boxes

    @property
    def label_uids(self):
        """The class labels of the *current* image."""
        return self.current.label_uids

    @property
    def ready(self):
        """Whether the *current* image has been marked as ready for export."""
        return self.current.ready

    @property
    def image_size(self):
        return self.current.img_size

    def __len__(self) -> int:
        """The number of images in the dataset."""
        return len(self.image_store)

    def _export_csv(self, path: str, data: list[SingleImage], delimiter: str = ";"):
        """Export the annotations to a CSV file.

        Args:
            path: The path to the output CSV file.
            data: The list of annotations to export.
            delimiter: The delimiter to use for separating fields in the CSV file.
        """
        if not path.endswith(".csv"):
            raise ValueError("Export path must be a CSV file.")

        with open(path, "w") as f:
            f.write(
                f"file_name{delimiter}center_x{delimiter}center_y{delimiter}width{delimiter}height{delimiter}label\n"
            )
            for a in data:
                for box, label_uid in zip(a.boxes, a.label_uids):
                    label = self.class_store.get_name(label_uid)
                    center_x, center_y, width, height = box
                    f.write(
                        f"{a.name}{delimiter}{center_x}{delimiter}{center_y}{delimiter}{width}{delimiter}{height}{delimiter}{label}\n"
                    )

    def _export_json(self, path: str):
        """Export the annotations to a JSON file.

        Args:
            path: The path to the output JSON file.
            data: The list of annotations to export.
        """
        if not path.endswith(".json"):
            raise ValueError("Export path must be a JSON file.")

        with open(path, "w") as f:
            json.dump(self.image_store.to_json(), f)

    def _export_yolo(self, path: str, train: list[SingleImage], test: list[SingleImage]):
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

        self._process_yolo(path, train, "train")
        self._process_yolo(path, test, "test")

        # create a yaml config file
        data_yaml = {
            "train": os.path.join(path, "train").replace("\\", "/"),
            "val": os.path.join(path, "test").replace("\\", "/"),
            "nc": len(self.class_store.get_class_names()),
            "names": {i: label for i, label in enumerate(self.class_store.get_class_names())},
        }

        with open(os.path.join(path, "data.yaml"), "w") as f:
            yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)

    def _process_yolo(self, path: str, raw_data: list[SingleImage], split: str):
        """Process the annotations for the YOLO format.

        Args:
            path: The path to the output directory.
            raw_data: The list of annotations to process.
            split: The split to process (train or test).
        """
        for i, data in enumerate(raw_data):
            img: Image.Image = Image.open(data.path)
            img = img.resize((640, 640))
            img.save(os.path.join(path, split, "images", f"{i}.jpg"))

            with open(os.path.join(path, split, "labels", f"{i}.txt"), "w") as f:
                for box, label_uid in zip(data.boxes, data.label_uids):
                    label = self.class_store.get_name(label_uid)
                    x_center, y_center, width, height = box

                    # write the label and the normalized box coordinates
                    label_idx = self.class_store.get_class_names().index(label)
                    f.write(f"{label_idx} {x_center} {y_center} {width} {height}\n")

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
