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
        self._current_uuid: UUID | None = self._images[0].uuid if len(self._images) > 0 else None
        if self._current_uuid is not None:
            self.active_image.init(self._detection_model)

    def add_images(self, images: list[SingleImage | str] | SingleImage | str) -> list[UUID]:
        """Add images to the store.

        Args:
            images: A list of `SingleImage` or image paths, or a single `SingleImage` or as single image path.
        """
        if not isinstance(images, list):
            images = [images]

        starting_empty = len(self._images) == 0

        new_uuids = []
        for img in images:
            if isinstance(img, str):
                img = SingleImage(img, os.path.basename(img), self._class_store)
            self._images.append(img)
            new_uuids.append(img.uuid)

        if starting_empty and len(new_uuids) > 0:
            self._current_uuid = new_uuids[0]
            self.active_image.init(self._detection_model)

        return new_uuids

    def delete_images(self, uuid: UUID | list[UUID]):
        """Delete images from the store.

        If the current image is deleted, the next image becomes the current image.

        Args:
            uuid: A single UUID or a list of UUIDs of the images to delete.
        """
        if not isinstance(uuid, list):
            uuid = [uuid]

        if not all(u in [img.uuid for img in self._images] for u in uuid):
            raise ValueError("One or more UUIDs are not in the image store.")
        
        if len(uuid) != len(set(uuid)):
            raise ValueError("Duplicate UUIDs provided.")

        if self._current_uuid in uuid and len(self._images) > 1:
            current_idx = self._images.index(
                next(img for img in self._images if img.uuid == self._current_uuid)
            )  # pragma: no cover

            # here we handle the current uuid, so we remove it from the list of uuids to delete
            uuid = [u for u in uuid if u != self._current_uuid]

            # make sure we select the next uuid from an index that is not out of bounds
            new_idx = current_idx + 1 if current_idx < len(self._images) - 1 else current_idx - 1
            self._current_uuid = self._images[new_idx].uuid
            del self._images[current_idx]

            # the uuid we handled here as already been removed from the list of uuids to delete
            self.delete_images(uuid)
        else:
            self._images = [img for img in self._images if img.uuid not in uuid]
            if len(self._images) == 0:
                self._current_uuid = None

    def activate_image(self, uuid: UUID):
        """Activate an image by its UUID."""
        if uuid not in [img.uuid for img in self._images]:
            raise ValueError("UUID not found in image store.")

        self._current_uuid = uuid

    def next(self):
        """Move to the next image in the dataset. If the end of the dataset is reached, do nothing.

        If the next image has not been seen before, initialize it with automatic annotation.
        """
        if self._current_uuid is None and len(self._images) > 0:
            self.jump_to(self._images[0].uuid)
            return
        
        if self._current_uuid is None:
            return

        current_idx = next(i for i, img in enumerate(self._images) if img.uuid == self._current_uuid)  # pragma: no cover
        if current_idx < len(self._images) - 1:
            uuid = self._images[current_idx + 1].uuid
            self.jump_to(uuid)

    def jump_to(self, uuid: UUID):
        """Jump to a specific image in the dataset.

        If the image has not been seen before, initialize it with automatic annotation.

        Args:
            uuid: The unique identifier of the image.

        Raises:
            ValueError: If the UUID is not found in the image store.
        """
        if uuid not in [img.uuid for img in self._images]:
            raise ValueError("UUID not found in image store.")

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
        """The UUID of the active image.
        
        This will always point to an image, unless the store is empty. In that case, it will be `None`. In
        other words, there can never be a `None` situation where the store is not empty.
        """
        return self._current_uuid

    @property
    def active_image(self) -> SingleImage:
        """The active image."""
        return self[self.active_uuid] if self.active_uuid is not None else None

    @property
    def image_names(self) -> list[str]:
        """A list of the image names."""
        return [img.name for img in self._images]

    def to_json(self):
        return [img.to_dict() for img in self._images]

    def __getitem__(self, uuid: UUID) -> SingleImage:
        if uuid not in [img.uuid for img in self._images]:
            raise ValueError("UUID not found in image store.")

        return next(img for img in self._images if img.uuid == uuid)  # pragma: no cover

    def __len__(self) -> int:
        return len(self._images)

    def __iter__(self):
        return iter(self._images)
