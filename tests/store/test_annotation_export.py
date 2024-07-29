"""Module for testing the annotation export functionality."""

from abc import ABC

from typing import cast

import os
import tempfile

import pandas as pd
import random

import unittest
from PIL import Image

from annotator.store.annotation_export import export
from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage
from annotator.model.mock_model import MockModel


def _cast(obj: list[SingleImage] | list[str] | list[SingleImage | str]) -> list[SingleImage | str]:
    return cast(list[SingleImage | str], obj)


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
        self.image_store = ImageStore(self.class_store, self.mock_model, _cast(self.image_paths))

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


class TestExportCSV(TestEnvironment):
    """Class for testing the CSV export functionality."""

    def setUp(self) -> None:
        """Set up the test case."""
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "test.csv")

    def tearDown(self) -> None:
        """Tear down the test case."""
        self.temp_dir.cleanup()

    def _ground_truth_to_df(self, ground_truth: list[SingleImage], seed: int) -> pd.DataFrame:
        """Convert the ground truth list of images to a DataFrame."""
        random.seed(seed)
        random.shuffle(ground_truth)

        lines = []
        for img in ground_truth:
            for box, label_uid in zip(img.boxes, img.label_uids):
                lines.append(
                    {
                        "path": img.path,
                        "file_name": img.name,
                        "center_x": box[0],
                        "center_y": box[1],
                        "width": box[2],
                        "height": box[3],
                        "label": self.class_store.get_name(label_uid),
                    }
                )
        return pd.DataFrame(lines)

    def _init_all_images(self, imgs: list[SingleImage]) -> None:
        """Initialize all images in the image store."""
        for img in imgs:
            img.init(self.mock_model)

    def _ready_all_images(self, imgs: list[SingleImage]) -> None:
        """Set all images in the image store to ready."""
        for img in imgs:
            img.ready = True

    def test_invalid_path(self) -> None:
        """Test exporting annotations to a CSV file with an invalid path."""
        with self.assertRaises(ValueError):
            export("invalid_path", "csv", self.image_store, self.class_store, True, 0.0)

    def test_no_split_all(self) -> None:
        """Test exporting annotations to a CSV file without a split and with all images.

        Here we expect the annotations to be all marked as training data. We do not exclude images that are
        not marked as ready in this test case.
        """
        # set the path to a file inside the temporary directory
        save_path = os.path.join(self.temp_dir.name, "test.csv")

        export(save_path, "csv", self.image_store, self.class_store, False, 0.0, 42)
        self.assertTrue(os.path.exists(self.temp_file))

        df_created = pd.read_csv(save_path, delimiter=";", header=0)
        df_true = self._ground_truth_to_df(self.ground_truth_img_list.copy(), 42)
        df_true["split"] = "train"
        pd.testing.assert_frame_equal(df_created, df_true)

        # add bounding Boxes to image 1
        self.image_store._images[1].add_box([0.6, 0.1, 0.2, 0.8], 0)
        self.image_store._images[1].add_box([0.3, 0.5, 0.4, 0.4], 1)
        self.ground_truth_img_list[1].add_box([0.6, 0.1, 0.2, 0.8], 0)
        self.ground_truth_img_list[1].add_box([0.3, 0.5, 0.4, 0.4], 1)

        export(save_path, "csv", self.image_store, self.class_store, False, 0.0, 0)
        df_created = pd.read_csv(save_path, delimiter=";", header=0)
        self.assertTrue(os.path.exists(self.temp_file))
        df_true = self._ground_truth_to_df(self.ground_truth_img_list.copy(), 0)
        df_true["split"] = "train"

        pd.testing.assert_frame_equal(df_created, df_true)

    def test_no_split_ready(self) -> None:
        """Test exporting annotations to a CSV file without a split and with ready images only.

        Here we expect the annotations to be all marked as training data. We exclude images that are not
        marked as ready.
        """
        for i in range(len(self.ground_truth_img_list)):
            self.ground_truth_img_list[i].init(self.mock_model)
            self.ground_truth_img_list[i].ready = i % 2 == 0
            self.image_store._images[i].init(self.mock_model)
            self.image_store._images[i].ready = i % 2 == 0

        save_path = os.path.join(self.temp_dir.name, "test.csv")
        export(save_path, "csv", self.image_store, self.class_store, True, 0.0, 42)
        self.assertTrue(os.path.exists(self.temp_file))
        df_created = pd.read_csv(save_path, delimiter=";", header=0)
        expected = [img for img in self.ground_truth_img_list if img.ready]
        df_true = self._ground_truth_to_df(expected, 42)
        df_true["split"] = "train"
        pd.testing.assert_frame_equal(df_created, df_true)

    def test_split_all(self) -> None:
        """Test exporting annotations to a CSV file with a split and with all images.

        Here we expect the annotations to be split into training and validation data. We do not exclude images
        that are not marked as ready in this test case.
        """
        for split in [0.25, 0.5, 0.75]:
            self.tearDown()
            self.setUp()
            save_path = os.path.join(self.temp_dir.name, "test.csv")
            self.assertFalse(os.path.exists(self.temp_file))

            # add an additional image to the image store so we have 4 images in total
            self.image_store.add_images(self.additional_images[0])
            self.ground_truth_img_list.append(self.additional_images[0])

            self._init_all_images(self.ground_truth_img_list)
            self._init_all_images(self.image_store._images)

            export(save_path, "csv", self.image_store, self.class_store, False, split, 42)
            self.assertTrue(os.path.exists(self.temp_file))
            df_created = pd.read_csv(save_path, delimiter=";", header=0)
            df_true = self._ground_truth_to_df(self.ground_truth_img_list.copy(), 42)
            df_true["split"] = ["train"] * int(16 * (1 - split)) + ["test"] * int(16 * split)
            pd.testing.assert_frame_equal(df_created, df_true)

    def test_split_ready(self) -> None:
        """Test exporting annotations to a CSV file with a split and with ready images only.

        Here we expect the annotations to be split into training and validation data. We exclude images that
        are not marked as ready.
        """
        for split in [0.25, 0.5, 0.75]:
            self.tearDown()
            self.setUp()
            save_path = os.path.join(self.temp_dir.name, "test.csv")
            self.assertFalse(os.path.exists(self.temp_file))

            # add an additional image to the image store so we have 4 images in total
            self.image_store.add_images(self.additional_images)
            self.ground_truth_img_list.append(self.additional_images[0])

            self._init_all_images(self.ground_truth_img_list)
            self._init_all_images(self.image_store._images)
            self._ready_all_images(self.ground_truth_img_list)
            self._ready_all_images(self.image_store._images)
            self.image_store._images[4].ready = False

            export(save_path, "csv", self.image_store, self.class_store, True, split, 42)
            self.assertTrue(os.path.exists(self.temp_file))
            df_created = pd.read_csv(save_path, delimiter=";", header=0)
            expected = [img for img in self.ground_truth_img_list if img.ready]
            df_true = self._ground_truth_to_df(expected, 42)
            df_true["split"] = ["train"] * int(16 * (1 - split)) + ["test"] * int(16 * split)
            pd.testing.assert_frame_equal(df_created, df_true)
