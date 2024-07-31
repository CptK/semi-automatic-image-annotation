"""The controller module for the annotator."""

from typing import Any, Literal, cast
from uuid import UUID

from annotator.model.base_model import DetectionModel
from annotator.store.annotation_export import export
from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage
from annotator.ui import UI


class Controller:
    """The controller for the annotator application.

    Args:
        store: The annotation store object to use for image data.

    Note:
    - It is required to set the view for the controller using the `set_view` method.
    """

    def __init__(
        self,
        classes: ClassesStore | list[str] | list[dict[str, str]],
        detection_model: DetectionModel,
        initial_images: list[SingleImage | str] = [],
    ):
        self._class_store = classes if isinstance(classes, ClassesStore) else ClassesStore(classes)
        self._img_store = ImageStore(self._class_store, detection_model, initial_images)

        self._view: UI

    def set_view(self, view: UI) -> None:
        """Set the view for the controller."""
        self._view = view

    def classes_store(self) -> ClassesStore:
        """The class store for the dataset."""
        return self._class_store

    def image_store(self):
        """The image store for the dataset."""
        return self._img_store

    def active_uuid(self):
        """The unique identifier of the *current* image."""
        return self._img_store.active_uuid

    def add_box(self, box: Any, label_uid: int, redraw: bool = True):
        """Add a new bounding box to the *current* image."""
        self._img_store.active_image.add_box(box, label_uid)  # type: ignore
        if redraw:
            self._view.redraw_content()
        self._view.refresh_right_sidebar()

    def image_names(self):
        """A list of file names of all images in the dataset."""
        return self._img_store.image_names

    def current(self) -> SingleImage | None:
        """The index of the *current* image in the dataset."""
        return self._img_store.active_image

    def is_ready(self, uuid: UUID):
        return self._img_store[uuid].ready

    def mark_ready(self):
        """Mark the *current* image as ready for export."""
        self._img_store.activate_image(self.active_uuid())
        self._view.refresh_left_sidebar()

    def next(self):
        """Move to the next image in the dataset."""
        self._img_store.next()
        self._view.refresh_all()

    def jump_to(self, uuid: UUID):
        """Jump to a specific image uuid."""
        self._img_store.jump_to(uuid)
        self._view.refresh_all()

    def add_images(self, paths: list[str]) -> list[UUID]:
        """Add images to the dataset."""
        new_uuids = self._img_store.add_images(cast(list[SingleImage | str], paths))
        self._view.refresh_all()
        return new_uuids

    def delete_image(self):
        """Delete the *current* image from the dataset."""
        self._img_store.delete_images(self.active_uuid())
        self._view.refresh_all()

    def export(self, path: str, format: Literal["json", "csv", "yolo"], ready_only: bool, test_split: float):
        """Export the annotations to disk."""
        export(path, format, self._img_store, self._class_store, ready_only, test_split)

    def available_labels(self):
        """The available labels for annotation."""
        return self._class_store.get_class_names()

    def available_class_uids(self):
        """The available class uids for annotation."""
        return self._class_store.get_class_uids()

    def change_image_annotation(
        self,
        idx: int,
        box: list[float] | tuple[float, float, float, float] | None = None,
        label_uid: int | None = None,
        redraw: bool = True,
    ):
        """Change the annotation for the *current* image at the given index."""
        self._img_store.change_image_annotation(self.active_uuid(), idx, box, label_uid)
        if redraw:
            self._view.redraw_content(only_boxes=True)  # type: ignore

    def delete(self, idx: int):
        """Delete the label for the bounding box at the given index."""
        self._img_store.active_image.delete_box(idx)  # type: ignore
        self._view.redraw_content(only_boxes=True)  # type: ignore

    def class_iter(self):
        """Iterate over the available classes."""
        return iter(self._class_store)

    def delete_class(self, uid: int, change_classes_uid: int | None = None, redraw: bool = True):
        """Delete a class from the dataset.

        Args:
            uid: The unique identifier of the class.
            change_classes_uid: The class to change bbox labels to. If None, the bboxes are deleted.
            redraw: Whether to redraw the content.
        """
        self._img_store.remove_label(uid, change_classes_uid)
        self._class_store.delete_class(uid)
        if redraw:
            self._view.redraw_content(only_boxes=True)  # type: ignore

    def set_default_class_uid(self, uid: int) -> None:
        """Set the default class uid."""
        self._class_store.set_default_uid(uid)

    def get_default_class_uid(self) -> int:
        """Get the default class uid."""
        return self._class_store.get_default_uid()

    def add_new_init_class(self) -> dict[str, Any]:
        """Add a new class to the dataset with default values."""
        return self._class_store.add_class(
            self._class_store.get_next_uid(),
            self._class_store.get_next_class_name(),
            self._class_store.get_next_color(),
            False,
        )

    def get_number_classes(self) -> int:
        """The number of classes in the dataset."""
        return len(self._class_store)

    def change_class_color(self, uid: int, color: str) -> None:
        """Change the color of a class."""
        self._class_store.change_color(uid, color)
        self._view.redraw_content(only_boxes=True)  # type: ignore

    def change_class_name(self, uid: int | list[int], name: str | list[str]) -> None:
        """Change the name of a class or a list of classes.

        Args:
            uid: The unique identifier of the class or a list of unique identifiers.
            name: The new name for the class or a list of new names.
        """
        self._class_store.change_name(uid, name)
        self._view.redraw_content(only_boxes=True)  # type: ignore
        self._view.refresh_right_sidebar()

    def get_class_color(self, uid: int) -> str:
        """Get the color of a class."""
        return self._class_store.get_color(uid)

    def get_class_name(self, uid: int) -> str:
        """Get the name of a class."""
        return self._class_store.get_name(uid)

    def get_class_uid(self, name: str) -> int:
        """Get the unique identifier of a class."""
        return self._class_store.get_uid(name)
