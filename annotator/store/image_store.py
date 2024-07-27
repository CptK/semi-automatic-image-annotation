"""A module for storing and managing `SingleImage` objects."""

import os
from uuid import UUID

from annotator.model.base_model import DetectionModel
from annotator.store.classes_store import ClassesStore
from annotator.store.single_image import SingleImage


class ImageStore:
    """A class for storing and managing `SingleImage` objects."""

    def __init__(
        self, class_store: ClassesStore, detection_model: DetectionModel, images: list[SingleImage | str] = []
    ):
        self._class_store = class_store
        self._detection_model = detection_model
        self._images: list[SingleImage] = []
        self.add_images(images)
        self._current_uuid: UUID = self._images[0].uuid

    def add_images(self, images: list[SingleImage | str] | SingleImage | str) -> list[UUID]:
        """Add images to the store.

        Args:
            images: A list of `SingleImage` or image paths, or a single `SingleImage` or as single image path.
        """
        if not isinstance(images, list):
            images = [images]

        new_uuids = []
        for img in images:
            if isinstance(img, str):
                img = SingleImage(img, os.path.basename(img), self._class_store)
            self._images.append(img)
            new_uuids.append(img.uuid)
        return new_uuids

    def delete_images(self, uuid: UUID | list[UUID]):
        """Delete images from the store.

        If the current image is deleted, the next image becomes the current image.

        Args:
            uuid: A single UUID or a list of UUIDs of the images to delete.
        """
        if not isinstance(uuid, list):
            uuid = [uuid]

        if self._current_uuid in uuid:
            current_idx = self._images.index(
                next(img for img in self._images if img.uuid == self._current_uuid)
            )
            # make sure we select the next uuid from an index that is not out of bounds
            new_idx = max(current_idx + 1, len(self._images) - 1)
            self._current_uuid = self._images[new_idx].uuid
            del self._images[current_idx]
            # make sure that the next image could also be among the ones to delete
            self.delete_images(uuid[1:])
        else:
            self._images = [img for img in self._images if img.uuid not in uuid]

    def activate_image(self, uuid: UUID):
        """Activate an image by its UUID."""
        self._current_uuid = uuid

    def next(self):
        """Move to the next image in the dataset. If the end of the dataset is reached, do nothing.

        If the next image has not been seen before, initialize it with automatic annotation.
        """
        current_idx = next(i for i, img in enumerate(self._images) if img.uuid == self._current_uuid)
        if current_idx < len(self._images) - 1:
            uuid = self._images[current_idx + 1].uuid
            self.jump_to(uuid)

    def jump_to(self, uuid: UUID):
        """Jump to a specific image in the dataset.

        If the image has not been seen before, initialize it with automatic annotation.

        Args:
            uuid: The unique identifier of the image.
        """
        self._current_uuid = uuid
        if not self.active_image.auto_intialized:
            self.active_image.init(self._detection_model)

    def remove_label(self, label_uid: int, new_label_uid: int | None = None):
        """Remove all bounding boxes with a certain label from the dataset.

        If a new label is provided, the bounding boxes are assigned to the new label. Otherwise, the bounding
        boxes are removed.

        Args:
            label_uid: The unique identifier of the label to remove.
            new_label_uid: The unique identifier of the new label to assign to the bounding boxes.
        """
        for img in self._images:
            if new_label_uid is not None:
                img.change_all_labels(label_uid, new_label_uid)
            else:
                img.delete_all_with_label(label_uid)

    @property
    def active_uuid(self) -> UUID:
        """The UUID of the active image."""
        return self._current_uuid

    @property
    def active_image(self) -> SingleImage:
        """The active image."""
        return self[self.active_uuid]

    @property
    def image_names(self) -> list[str]:
        """A list of the image names."""
        return [img.name for img in self._images]

    def to_json(self):
        return [img.to_dict() for img in self._images]

    def __getitem__(self, uuid: UUID) -> SingleImage:
        return next(img for img in self._images if img.uuid == uuid)

    def __len__(self) -> int:
        return len(self._images)

    def __iter__(self):
        return iter(self._images)
