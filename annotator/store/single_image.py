"""A module for storing annotations for a single image."""

from uuid import UUID, uuid4

from PIL import Image

from annotator.model.base_model import DetectionModel
from annotator.store.classes_store import ClassesStore


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
        self.__uuid = uuid4()

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

    def change_label(self, idx: int, label_uid: int) -> None:
        """Change the label of a bounding box in the image.

        Args:
            idx: The index of the bounding box to change.
            label_uid: The unique identifier of the new label.
        """
        self.label_uids[idx] = label_uid

    def delete(self, idx: int) -> None:
        """Delete a bounding box from the image.

        Args:
            idx: The index of the bounding box to delete.
        """
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

    def delete_all_with_label(self, label_uid: int) -> None:
        """Delete all bounding boxes with a certain label from the image.

        Args:
            label_uid: The unique identifier of the label to delete.
        """
        self.boxes = [box for i, box in enumerate(self.boxes) if self.label_uids[i] != label_uid]
        self.label_uids = [label for label in self.label_uids if label != label_uid]

    def change_all_labels(self, old_label_uid: int, new_label_uid: int) -> None:
        """Change all labels of a certain type to a new label for the image.

        Args:
            old_label_uid: The unique identifier of the label to change.
            new_label_uid: The unique identifier of the new label.
        """
        self.label_uids = [new_label_uid if label == old_label_uid else label for label in self.label_uids]

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

    @property
    def uuid(self) -> UUID:
        return self.__uuid
