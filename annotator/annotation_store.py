"""This module provides a class for storing and managing annotations."""

import json
import os
from typing import Any, Literal

import yaml
from PIL import Image


class ClassesStore:
    """A class for storing and managing object classes.

    Each class is represented as a dictionary with the keys
    - 'uid': The unique identifier of the class.
    - 'name': The name of the class.
    - 'color': The color of the class.
    - 'default': Whether the class is the default class.

    Args:
        classes: A list of class dictionaries or class names.
    """

    DEFAULT_COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF"]

    def __init__(self, classes: list[dict[str, str]] | list[str]):
        self.classes: list[dict[str, Any]] = []

        if isinstance(classes[0], str):
            for i, name in enumerate(classes):
                self.add_class(
                    i, str(name), self.DEFAULT_COLORS[len(self.classes) % len(self.DEFAULT_COLORS)], i == 0
                )
        else:
            self.classes = classes  # type: ignore
            if not any(cls["default"] for cls in self.classes):
                self.classes[0]["default"] = True
            # if there is more than one default, only the first one is kept
            if sum(cls["default"] for cls in self.classes) > 1:
                first_default_idx = next(i for i, cls in enumerate(self.classes) if cls["default"])
                for i, cls in enumerate(self.classes):
                    if i != first_default_idx:
                        cls["default"] = False

    def add_class(self, uid: int, name: str, color: str, is_default: bool = False) -> dict[str, Any]:
        """Add a class to the store.

        Args:
            uid: The unique identifier of the class.
            name: The name of the class.
            color: The color of the class.
            is_default: Whether the class is the default class.

        Returns:
            The dictionary representing the new class.

        Raises:
            ValueError: If a class with the same UID or name already exists, or if more than one class is set
                        as default.
        """
        if any(cls["uid"] == uid for cls in self.classes):
            raise ValueError("Class with the same UID already exists.")

        if any(cls["name"] == name for cls in self.classes):
            raise ValueError("Class with the same name already exists.")

        if is_default and any(cls["default"] for cls in self.classes):
            raise ValueError("Only one class can be the default class.")

        self.classes.append({"uid": uid, "name": name, "color": color, "default": is_default})
        return self.classes[-1]

    def delete_class(self, uid: int) -> None:
        """Delete a class from the store.

        If the class is the default class, the first class in the list is set as the new default.

        Args:
            uid: The unique identifier of the class.
        """
        self.classes = [cls for cls in self.classes if cls["uid"] != uid]
        if not any(cls["default"] for cls in self.classes):
            self.classes[0]["default"] = True

    def get_class_names(self) -> list[str]:
        """Returns a list of all class names."""
        return [cls["name"] for cls in self.classes]

    def get_class_uids(self) -> list[int]:
        """Returns a list of all class UIDs."""
        return [cls["uid"] for cls in self.classes]

    def get_next_color(self) -> str:
        """Returns the next color in the default color list."""
        return self.DEFAULT_COLORS[len(self.classes) % len(self.DEFAULT_COLORS)]

    def get_next_class_name(self) -> str:
        """Returns the next class name in the default naming scheme."""
        name = f"Class {len(self.classes) + 1}"
        while any(item == name for item in self.get_class_names()):
            name = f"Class {int(name.split()[-1]) + 1}"
        return name

    def get_next_uid(self) -> int:
        """Returns the next available unique identifier."""
        ids = [cls["uid"] for cls in self.classes]
        return int(max(ids)) + 1 if ids else 0

    def get_default_uid(self) -> int:
        """Returns the unique identifier of the default class."""
        return int(next(cls["uid"] for cls in self.classes if cls["default"]))

    def set_default_uid(self, uid: int) -> None:
        """Set the default class by its unique identifier. The previous default class is unset."""
        default_class = next(cls for cls in self.classes if cls["default"])
        default_class["default"] = False
        next(cls for cls in self.classes if cls["uid"] == uid)["default"] = True

    def get_color(self, uid: int) -> str:
        """Returns the color of a class by its unique identifier."""
        return str(next(cls["color"] for cls in self.classes if cls["uid"] == uid))

    def get_default_class(self) -> dict[str, Any]:
        """Returns the default class."""
        return next(cls for cls in self.classes if cls["default"])

    def change_name(self, uid: int | list[int], name: str | list[str]) -> None:
        """Change the name of a class or a list of classes by their unique identifiers.

        Args:
            uid: The unique identifier of the class or a list of unique identifiers.
            name: The new name of the class or a list of new names.

        Raises:
            ValueError: If the number of UIDs and names do not match.
        """
        if isinstance(uid, int):
            uid = [uid]
            name = [name]  # type: ignore

        if len(uid) != len(name):
            raise ValueError("Number of UIDs and names do not match.")

        for i, n in zip(uid, name):
            next(cls for cls in self.classes if cls["uid"] == i)["name"] = n

    def change_color(self, uid: int, color: str) -> None:
        """Change the color of a class by its unique identifier."""
        next(cls for cls in self.classes if cls["uid"] == uid)["color"] = color

    def get_name(self, uid: int) -> str:
        """Returns the name of a class by its unique identifier."""
        return str(next(cls["name"] for cls in self.classes if cls["uid"] == uid))

    def get_uid(self, name: str) -> int:
        """Returns the unique identifier of a class by its name"""
        return int(next(cls["uid"] for cls in self.classes if cls["name"] == name))

    def __getitem__(self, idx: int):
        return self.classes[idx]

    def __len__(self):
        return len(self.classes)

    def __iter__(self):
        return iter(self.classes)


class DetectionModel:
    """A class for object detection using a PyTorch model.

    The ouput format of the model should be a list of dictionaries, each containing the keys
    - 'box' for the bounding box coordinates in the format [x1, y1, x2, y2],
    - 'boxn' for the normalized bounding box coordinates in the format [x1, y1, x2, y2],
    - 'label' for the class label,
    - 'confidence' for the detection confidence.

    Args:
        model: The PyTorch model to use for object detection.
        available_labels: A list of available class labels.
        input_size: The size to which to resize the input images.
    """

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

    def __init__(self, path: str, name: str, class_store: ClassesStore) -> None:
        self.path = path
        self.name = name
        self.class_store = class_store
        self.boxes: list = []
        self.label_uids: list[int] = []
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
                self.label_uids = self.labels_to_uids([r["label"] for r in res])
                self.auto_intialized = True
            except Exception as e:
                print(f"Failed to initialize image: {e}")

    def mark_ready(self):
        """Mark the image as ready for export."""
        self.ready = True

    def change_label(self, idx, label_uid: int):
        """Change the label of a bounding box in the image."""
        self.label_uids[idx] = label_uid

    def delete(self, idx):
        """Delete a bounding box from the image."""
        self.boxes.pop(idx)
        self.label_uids.pop(idx)

    def add_box(self, box, label_uid: int):
        """Add a bounding box to the image."""
        self.boxes.append(box)
        self.label_uids.append(label_uid)

    def labels_to_uids(self, labels: list[str]) -> list[int]:
        """Convert a list of class labels to a list of unique identifiers.

        In case a label is not found in the class store, the default class is used.

        Args:
            labels: A list of class labels.

        Returns:
            A list of unique identifiers corresponding to the class labels.
        """
        uids = []
        for label in labels:
            if label in self.class_store.get_class_names():
                uids.append(self.class_store.get_uid(label))
            else:
                uids.append(self.class_store.get_default_uid())
        return uids

    def uids_to_labels(self, uids: list[int]):
        """Convert a list of unique identifiers to a list of class labels.

        Args:
            uids: A list of unique identifiers.

        Returns:
            A list of class labels corresponding to the unique identifiers.
        """
        labels = []
        for uid in uids:
            labels.append(self.class_store.get_name(uid))
        return labels

    def to_dict(self):
        return {
            "file_path": self.path,
            "file_name": self.name,
            "boxes": self.boxes,
            "labels": self.uids_to_labels(self.label_uids),
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
        self.class_store = ClassesStore(available_labels)
        self.model = DetectionModel(model, available_labels)
        self.data_path = data_path

        self.annotations = [SingleImage(os.path.join(data_path, f), f, self.class_store) for f in img_files]

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

    def change_label(self, idx, label_uid: int):
        """Change the label of a bounding box in the *current* image."""
        self.current.change_label(idx, label_uid)

    def change_all_labels(self, old_label_uid: int, new_label_uid: int):
        """Change all labels of a certain type to a new label in the *current* image."""
        for img in self.annotations:
            for i, label_uid in enumerate(img.label_uids):
                if label_uid == old_label_uid:
                    img.label_uids[i] = new_label_uid

    def delete(self, idx):
        """Delete a bounding box from the *current* image."""
        self.current.delete(idx)

    def delete_all_with_label(self, label_uid: int):
        """Delete all bounding boxes with a certain label from the *current* image."""
        for annotation in self.annotations:
            annotation.boxes = [
                box for i, box in enumerate(annotation.boxes) if annotation.label_uids[i] != label_uid
            ]
            annotation.label_uids = [label for label in annotation.label_uids if label != label_uid]

    def add_box(self, box, label_uid: int | None = None):
        """Add a bounding box to the *current* image."""
        if label_uid is None:
            label_uid = self.class_store.get_default_uid()
        self.current.add_box(box, label_uid)

    def change_box(self, idx, box):
        """Change the coordinates of a bounding box in the *current* image."""
        self.current.boxes[idx] = box

    def add_images(self, paths: list[str]):
        """Add images to the dataset.

        Args:
            paths: A list of paths to the image files.
        """
        for path in paths:
            name = os.path.basename(path)
            if not self.annotation_by_name(name):
                self.annotations.append(SingleImage(path, name, self.class_store))

    def delete_image(self):
        """Delete the *current* image from the dataset."""
        del self.annotations[self.current_index]
        if self.current_index >= len(self.annotations):
            self.current_index = len(self.annotations) - 1

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
    def label_uids(self):
        """The class labels of the *current* image."""
        return self.current.label_uids

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
        return [a.to_dict() for a in self.annotations]

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
            img: Image.Image = Image.open(os.path.join(self.data_path, data.name))
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
            self.annotations.extend(new_annotations)
        else:
            self.annotations = new_annotations
            self.current_index = 0
            self.jump_to(self.current_index)
