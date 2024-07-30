"""Base environment for setting up the test environment."""

import os
import unittest
from abc import ABC
from typing import cast

from annotator.model.mock_model import MockModel
from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage


class TestEnvironment(unittest.TestCase, ABC):
    """Class for setting up the test environment."""

    def setUp(self) -> None:
        """Set up the test environment."""
        # Set up the classes store
        self.class_store = ClassesStore(["class1", "class2", "class3"])

        # Set up the mock model
        self.mock_bboxes = [
            [0.1, 0.1, 0.2, 0.2],
            [0.3, 0.3, 0.4, 0.4],
            [0.5, 0.5, 0.6, 0.6],
            [0.7, 0.7, 0.8, 0.8],
        ]
        self.mock_scores = [0.9, 0.8, 0.7, 1]
        self.mock_labels = ["class3", "class1", "class2", "class3"]
        self.img_size = (640, 640)
        self.mock_model = MockModel(self.mock_bboxes, self.mock_labels, self.mock_scores, self.img_size)

        # Set up the path to the test images
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "images"))

        # Set up the test image store
        self.image_names = ["test_img_1.JPEG", "test_img_2.JPEG", "test_img_3.JPEG"]
        self.image_paths = [os.path.join(self.base_path, img_name) for img_name in self.image_names]
        self.images = [
            SingleImage(img_path, os.path.basename(img_path), self.class_store)
            for img_path in self.image_paths
        ]
        self.image_store = ImageStore(self.class_store, self.mock_model, self.cast(self.image_paths))

        # Set up additional images that can be used for additional testing
        self.additional_image_names = ["test_img_4.JPEG", "test_img_5.JPEG"]
        self.additional_image_paths = [
            os.path.join(self.base_path, img_name) for img_name in self.additional_image_names
        ]
        self.additional_images = [
            SingleImage(os.path.join(self.base_path, img_name), img_name, self.class_store)
            for img_name in self.additional_image_names
        ]

        # Initialize the ground truth image list (i.e. the list that is expected to be in the image store
        # upon initialization). This list can be a base for comparison with the actual image store.
        self.ground_truth_img_list = [
            SingleImage(img_path, os.path.basename(img_path), self.class_store)
            for img_path in self.image_paths
        ]
        self.ground_truth_img_list[0].init(self.mock_model)

    def init_all_images(self, imgs: list[SingleImage]) -> None:
        """Initialize all images in the image store."""
        for img in imgs:
            img.init(self.mock_model)

    def ready_all_images(self, imgs: list[SingleImage]) -> None:
        """Set all images in the image store to ready."""
        for img in imgs:
            img.ready = True

    def cast(self, obj: list[SingleImage] | list[str] | list[SingleImage | str]) -> list[SingleImage | str]:
        """Cast the object to a list of SingleImage or str."""
        return cast(list[SingleImage | str], obj)
