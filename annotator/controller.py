"""The controller module for the annotator."""

from typing import Any, Literal

from annotator.annotation_store import AnnotationStore, ClassesStore, SingleImage
from annotator.ui import UI


class Controller:
    """The controller for the annotator application.

    Args:
        store: The annotation store object to use for image data.

    Note:
    - It is required to set the view for the controller using the `set_view` method.
    """

    def __init__(self, store: AnnotationStore):
        self._store = store
        self._view: UI | None = None

    def set_view(self, view: UI):
        """Set the view for the controller."""
        self._view = view

    def classes_store(self) -> ClassesStore:
        """The class store for the dataset."""
        return self._store.class_store

    def current_index(self) -> int:
        """The index of the *current* image in the dataset."""
        return self._store.current_index

    def current_boxes(self):
        """The bounding boxes of the *current* image."""
        return self._store.boxes

    def current_label_uids(self):
        """The labels of the *current* image."""
        return self._store.label_uids

    def add_box(self, box: Any, label_uid: int, redraw: bool = True):
        """Add a new bounding box to the *current* image."""
        self._store.add_box(box, label_uid)
        if redraw:
            self._view.redraw_content()  # type: ignore
        self._view.refresh_right_sidebar()  # type: ignore

    def image_names(self):
        """A list of file names of all images in the dataset."""
        return self._store.image_names

    def current(self) -> SingleImage:
        """The index of the *current* image in the dataset."""
        return self._store.current

    def current_file_path(self):
        """The absolute file path of the *current* image."""
        return self._store.file_path

    def current_image_size(self):
        """The size of the *current* image."""
        return self._store.image_size

    def ready(self):
        """Whether the *current* image has been marked as ready for export."""
        return self._store.ready

    def mark_ready(self):
        """Mark the *current* image as ready for export."""
        self._store.mark_ready()
        self._view.refresh_left_sidebar()  # type: ignore

    def next(self):
        """Move to the next image in the dataset."""
        self._store.next()
        self._view.refresh_all()  # type: ignore

    def jump_to(self, idx: int):
        """Jump to a specific image index."""
        self._store.jump_to(idx)
        self._view.refresh_all()  # type: ignore

    def export(self, path: str, format: Literal["json", "csv", "yolo"], ready_only: bool, train_split: float):
        """Export the annotations to disk."""
        self._store.export(path, format, ready_only, train_split)

    def available_labels(self):
        """The available labels for annotation."""
        return self._store.class_store.get_class_names()

    def available_class_uids(self):
        """The available class uids for annotation."""
        return self._store.class_store.get_class_uids()

    def change_label(self, idx: int, label_uid: int):
        """Change the label for the given index."""
        self._store.change_label(idx, label_uid)
        self._view.redraw_content(only_boxes=True)  # type: ignore

    def change_box(self, idx: int, box: Any, redraw: bool = True):
        """Change the bounding box for the given index."""
        self._store.change_box(idx, box)
        if redraw:
            self._view.redraw_content(only_boxes=True)  # type: ignore

    def delete(self, idx: int):
        """Delete the label for the given index."""
        self._store.delete(idx)
        self._view.redraw_content(only_boxes=True)  # type: ignore

    def class_iter(self):
        """Iterate over the available classes."""
        return iter(self._store.class_store)

    def delete_class(self, uid: int, change_classes_uid: int | None = None, redraw: bool = True):
        """Delete a class from the dataset.

        Args:
            uid: The unique identifier of the class.
            change_classes_uid: The class to change bbox labels to. If None, the bboxes are deleted.
            redraw: Whether to redraw the content.
        """
        if change_classes_uid is None:
            self._store.delete_all_with_label(uid)
        else:
            self._store.change_all_labels(uid, change_classes_uid)
        self._store.class_store.delete_class(uid)
        if redraw:
            self._view.redraw_content(only_boxes=True)  # type: ignore

    def set_default_class_uid(self, uid: int) -> None:
        """Set the default class uid."""
        self._store.class_store.set_default_uid(uid)

    def get_default_class_uid(self) -> int:
        """Get the default class uid."""
        return self._store.class_store.get_default_uid()

    def add_new_init_class(self) -> dict[str, Any]:
        """Add a new class to the dataset with default values."""
        return self._store.class_store.add_class(
            self._store.class_store.get_next_uid(),
            self._store.class_store.get_next_class_name(),
            self._store.class_store.get_next_color(),
            False,
        )

    def get_number_classes(self) -> int:
        """The number of classes in the dataset."""
        return len(self._store.class_store)

    def change_class_color(self, uid: int, color: str) -> None:
        """Change the color of a class."""
        self._store.class_store.change_color(uid, color)
        self._view.redraw_content(only_boxes=True)  # type: ignore

    def change_class_name(self, uid: int | list[int], name: str | list[str]) -> None:
        """Change the name of a class or a list of classes.

        Args:
            uid: The unique identifier of the class or a list of unique identifiers.
            name: The new name for the class or a list of new names.
        """
        self._store.class_store.change_name(uid, name)
        self._view.redraw_content(only_boxes=True)  # type: ignore
        self._view.refresh_right_sidebar()  # type: ignore

    def get_class_color(self, uid: int) -> str:
        """Get the color of a class."""
        return self._store.class_store.get_color(uid)

    def get_class_name(self, uid: int) -> str:
        """Get the name of a class."""
        return self._store.class_store.get_name(uid)

    def get_class_uid(self, name: str) -> int:
        """Get the unique identifier of a class."""
        return self._store.class_store.get_uid(name)

    def __len__(self) -> int:
        """The number of images in the dataset."""
        return len(self._store)

    def __getitem__(self, idx: int) -> SingleImage:
        """Get the image at the given index."""
        return self._store[idx]
