"""This module provides a class for storing and managing annotations."""

import json
import os
from typing import Literal

from PIL import Image
import yaml


class DetectionModel:

    def __init__(self, model, available_labels: list[str], input_size: tuple[int, int] = (640, 640)):
        self.model = model
        self.available_labels = available_labels
        self.input_size = input_size

    def __call__(self, img: Image.Image):
        """Detect objects in a single image and return the results as a list of dictionaries.

        Args:
            img: The image to process.

        Returns:
            A list of dictionaries, each containing the keys 'box' for the bounding box coordinates, 'boxn'
            for the normalized bounding box coordinates, 'label' for the class label, and 'confidence' for the
            detection confidence.
        """
        img = img.resize(self.input_size)
        results = self.model(img)[0]
        labels = results.names
        boxes = results.boxes
        res = []
        for box in boxes:
            label = labels[box.cls.item()]
            if label not in self.available_labels:
                label = "none"

            # convert [x1, y1, x2, y2] to [center_x, center_y, width, height], all normalized to [0, 1]
            boxn = box.xyxyn[0].tolist()
            boxn = [(boxn[0] + boxn[2]) / 2, (boxn[1] + boxn[3]) / 2, boxn[2] - boxn[0], boxn[3] - boxn[1]]

            res.append(
                {
                    "box": box.xyxy[0].tolist(),
                    "boxn": boxn,
                    "label": label,
                    "confidence": box.conf.item(),
                }
            )
        return res


class SingleImage:
    """A class for storing annotations for a single image.

    Args:
        path: The path to the image file. (including the file name)
        name: The file name of the image.
        model: The object detection model to use for automatic annotation.
        available_labels: A list of available class labels.
        img_size: The size to which to resize the image for automatic annotation.

    Attributes:
        path: The path to the image file. (including the file name)
        name: The file name of the image.
        boxes: A list of bounding boxes in the image. Each box is represented as a list of four entries
            [center_x, center_y, width, height], where all values are normalized to the range [0, 1].
        labels: A list of class labels corresponding to the bounding boxes.
        ready: Whether the image has been marked as ready for export.
        skip: Whether the image should be skipped during annotation.
        auto_intialized: Whether the image has been automatically initialized with annotations.
        model: The object detection model to use for automatic annotation.
        available_labels: A list of available class labels.
        img_size: The size to which to resize the image for automatic annotation.
    """

    def __init__(self, path: str, name: str) -> None:
        self.path = path
        self.name = name
        self.boxes: list = []
        self.labels: list = []
        self.ready = False
        self.skip = False
        self.auto_intialized = False
        img = Image.open(self.path)
        self.img_size = img.size

    def init(self, model: DetectionModel | None):
        """Initialize the image with automatic annotation using the object detection model."""
        if self.auto_intialized:
            return
        if model is not None:
            try:
                img = Image.open(self.path)
                res = model(img)
                self.boxes = [r["boxn"] for r in res]
                self.labels = [r["label"] for r in res]
                self.auto_intialized = True
            except Exception as e:
                print(f"Failed to initialize image: {e}")

    def mark_ready(self):
        """Mark the image as ready for export."""
        self.ready = True

    def change_label(self, idx, label):
        """Change the label of a bounding box in the image."""
        self.labels[idx] = label

    def delete(self, idx):
        """Delete a bounding box from the image."""
        self.boxes.pop(idx)
        self.labels.pop(idx)

    def add_box(self, box, label="none"):
        """Add a bounding box to the image."""
        self.boxes.append(box)
        self.labels.append(label)

    def __dict__(self):
        return {
            "file_path": self.path,
            "file_name": self.name,
            "boxes": self.boxes,
            "labels": self.labels,
            "ready": self.ready,
            "skip": self.skip,
        }


class AnnotationStore:
    """A class for storing and managing annotations.

    Args:
        data_path: The path to the directory containing the images.
        model: The object detection model to use for automatic annotation.
        available_labels: A list of available class labels.
    """

    def __init__(self, data_path: str, model, available_labels: list[str]):
        img_files = [f for f in os.listdir(data_path)]
        self.model = DetectionModel(model, available_labels)
        self.data_path = data_path
        self.available_labels = available_labels

        self.annotations = [SingleImage(os.path.join(data_path, f), f) for f in img_files]

        self.current_index: int = 0
        self.jump_to(self.current_index)

    def next(self):
        """Move to the next image in the dataset. If the end of the dataset is reached, do nothing.

        If the next image has not been seen before, initialize it with automatic annotation.
        """
        self.jump_to(min(self.current_index + 1, len(self) - 1))

    def jump_to(self, index: int):
        """Jump to a specific image in the dataset.

        If the image has not been seen before, initialize it with automatic annotation.

        Args:
            index: The index of the image to jump to.
        """
        self.current_index = index
        if not self.current.auto_intialized:
            self.current.init(self.model)

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
        data = [a for a in self.annotations if not only_ready or a.ready]
        if format.lower() == "csv":
            self._export_csv(path, data)
        elif format.lower() == "json":
            self._export_json(path)
        elif format.lower() == "yolo":
            train = data[: int(len(data) * train_split)]
            test = data[int(len(data) * train_split) :]
            self._export_yolo(path, train, test)

    def annotation_by_name(self, name):
        """Get the index of the annotation with the specified file name.

        Args:
            name: The file name of the image.

        Returns:
            The index of the annotation with the specified file name, or None if not found.
        """
        for i, a in enumerate(self.annotations):
            if a.name == name:
                return i
        return None

    def mark_ready(self):
        """Mark the *current* image as ready for export."""
        self.current.ready = True

    def change_label(self, idx, label):
        """Change the label of a bounding box in the *current* image."""
        self.current.change_label(idx, label)

    def delete(self, idx):
        """Delete a bounding box from the *current* image."""
        self.current.delete(idx)

    def add_box(self, box, label="none"):
        """Add a bounding box to the *current* image."""
        self.current.add_box(box, label)

    def change_box(self, idx, box):
        """Change the coordinates of a bounding box in the *current* image."""
        self.current.boxes[idx] = box

    @property
    def current(self) -> SingleImage:
        """The index of the *current* image in the dataset."""
        return self.annotations[self.current_index]

    @property
    def file_path(self):
        """The absolute file path of the *current* image."""
        return self.current.path

    @property
    def boxes(self):
        """The bounding boxes of the *current* image."""
        return self.current.boxes

    @property
    def labels(self):
        """The class labels of the *current* image."""
        return self.current.labels

    @property
    def ready(self):
        """Whether the *current* image has been marked as ready for export."""
        return self.current.ready

    @property
    def image_names(self):
        """A list of file names of all images in the dataset."""
        return [a.name for a in self.annotations]

    @property
    def to_json(self):
        return [a.__dict__() for a in self.annotations]

    @property
    def image_size(self):
        return self.current.img_size

    def __getitem__(self, idx: int) -> SingleImage:
        """Get the image at the given index."""
        return self.annotations[idx]

    def __len__(self) -> int:
        """The number of images in the dataset."""
        return len(self.annotations)

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
                for box, label in zip(a.boxes, a.labels):
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
            json.dump(self.to_json, f)

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
            "nc": len(self.available_labels),
            "names": {i: label for i, label in enumerate(self.available_labels)},
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
            img = Image.open(os.path.join(self.data_path, data.name))
            img = img.resize((640, 640))
            img.save(os.path.join(path, split, "images", f"{i}.jpg"))

            with open(os.path.join(path, split, "labels", f"{i}.txt"), "w") as f:
                for box, label in zip(data.boxes, data.labels):
                    x_center, y_center, width, height = box

                    # write the label and the normalized box coordinates
                    f.write(f"{self.available_labels.index(label)} {x_center} {y_center} {width} {height}\n")

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

        new_annotations = [SingleImage(a["file_path"], a["file_name"]) for a in data]

        if append:
            self.annotations.extend(new_annotations)
        else:
            self.annotations = new_annotations
            self.current_index = 0
            self.jump_to(self.current_index)
