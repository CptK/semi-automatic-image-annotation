"""This module tests the image store."""

import os
import unittest
from typing import cast
from uuid import uuid4

from annotator.model.mock_model import MockModel
from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage


def _cast(obj: list[SingleImage] | list[str] | list[SingleImage | str]) -> list[SingleImage | str]:
    return cast(list[SingleImage | str], obj)


class TestImageStore(unittest.TestCase):
    """A class for testing the image store."""

    def setUp(self) -> None:
        self.class_store = ClassesStore(["class1", "class2", "class3"])
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

        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "images"))
        self.image_names = ["test_img_1.JPEG", "test_img_2.JPEG", "test_img_3.JPEG"]
        self.additional_image_names = ["test_img_4.JPEG", "test_img_5.JPEG"]
        self.additional_image_paths = [
            os.path.join(self.base_path, img_name) for img_name in self.additional_image_names
        ]
        self.additional_images = [
            SingleImage(os.path.join(self.base_path, img_name), img_name, self.class_store)
            for img_name in self.additional_image_names
        ]
        self.image_paths = [os.path.join(self.base_path, img_name) for img_name in self.image_names]
        self.images = [
            SingleImage(img_path, os.path.basename(img_path), self.class_store)
            for img_path in self.image_paths
        ]

        self.ground_truth_img_list = [
            SingleImage(img_path, os.path.basename(img_path), self.class_store)
            for img_path in self.image_paths
        ]
        self.ground_truth_img_list[0].init(self.mock_model)

        self.image_store = ImageStore(self.class_store, self.mock_model, _cast(self.image_paths))

    def _check_img_lists_equal(self, img_list: list[SingleImage], true_img_list: list[SingleImage]) -> None:
        for img, true_img in zip(img_list, true_img_list):
            self.assertEqual(type(img), type(true_img))
            self.assertEqual(img.path, true_img.path)
            self.assertEqual(img.name, true_img.name)
            self.assertEqual(img.class_store, true_img.class_store)
            self.assertFalse(img.ready)
            self.assertEqual(img.auto_intialized, true_img.auto_intialized)
            self.assertEqual(img.img_size, true_img.img_size)
            self.assertEqual(img.boxes, true_img.boxes)
            self.assertEqual(img.label_uids, true_img.label_uids)

    def test_init_empty(self) -> None:
        self.image_store = ImageStore(self.class_store, self.mock_model)
        self.assertEqual(self.image_store._images, [])
        self.assertIsNone(self.image_store._current_uuid)

    def test_init_paths(self) -> None:
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_add_images(self) -> None:
        self.image_store = ImageStore(self.class_store, self.mock_model, _cast(self.images))
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_add_single_image(self) -> None:
        new_img_path = os.path.join(self.base_path, self.additional_image_names[0])
        self.image_store.add_images(new_img_path)
        new_img = SingleImage(new_img_path, self.additional_image_names[0], self.class_store)
        ground_truth = self.ground_truth_img_list + [new_img]
        self._check_img_lists_equal(self.image_store._images, ground_truth)

        new_img_path = os.path.join(self.base_path, self.additional_image_names[1])
        new_img = SingleImage(new_img_path, self.additional_image_names[1], self.class_store)
        self.image_store.add_images(new_img)
        ground_truth.append(new_img)
        self._check_img_lists_equal(self.image_store._images, ground_truth)

    def test_add_multiple_image_paths(self) -> None:
        """Test adding multiple images by providing only their paths."""
        new_img_paths = [os.path.join(self.base_path, img_name) for img_name in self.additional_image_names]
        self.image_store.add_images(_cast(new_img_paths))
        new_imgs = [
            SingleImage(img_path, os.path.basename(img_path), self.class_store) for img_path in new_img_paths
        ]
        ground_truth = self.ground_truth_img_list + new_imgs
        self._check_img_lists_equal(self.image_store._images, ground_truth)

    def test_add_multiple_images(self) -> None:
        """Test adding multiple images by providing the images themselves."""
        new_imgs = [
            SingleImage(img_path, os.path.basename(img_path), self.class_store)
            for img_path in self.image_paths
        ]
        self.image_store.add_images(_cast(new_imgs))
        ground_truth = self.ground_truth_img_list + new_imgs
        self._check_img_lists_equal(self.image_store._images, ground_truth)

    def test_add_multiple_mixed(self) -> None:
        """Test adding multiple images by providing a mix of paths and images."""
        new_img_path_1 = os.path.join(self.base_path, self.additional_image_names[0])
        new_img_path_2 = os.path.join(self.base_path, self.additional_image_names[1])
        new_img_1 = SingleImage(new_img_path_1, self.additional_image_names[0], self.class_store)
        new_img_2 = SingleImage(new_img_path_2, self.additional_image_names[1], self.class_store)
        self.image_store.add_images([new_img_1, new_img_path_2])
        ground_truth = self.ground_truth_img_list + [new_img_1, new_img_2]
        self._check_img_lists_equal(self.image_store._images, ground_truth)

    def test_add_from_empty_store(self) -> None:
        """Test adding images to an empty store."""
        self.image_store = ImageStore(self.class_store, self.mock_model)
        self.image_store.add_images(_cast(self.images))
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_delete_invalid_uuid(self) -> None:
        """Test deleting an invalid UUID."""
        with self.assertRaises(ValueError):
            self.image_store.delete_images(uuid4())

        with self.assertRaises(ValueError):
            self.image_store.delete_images([self.image_store._images[0].uuid, uuid4()])

    def test_delete_single_not_active(self) -> None:
        """Test deleting a single image that is not active."""
        self.image_store.delete_images(self.image_store._images[1].uuid)
        ground_truth = [self.ground_truth_img_list[0], self.ground_truth_img_list[2]]
        self._check_img_lists_equal(self.image_store._images, ground_truth)

    def test_delete_single_active_first(self) -> None:
        """Test deleting the first image, that is also the active image.

        By default the first image is active."""
        self.image_store.delete_images(self.image_store._images[0].uuid)
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list[1:])
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

        self.image_store.delete_images(self.image_store._images[0].uuid)
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list[2:])
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

        self.image_store.delete_images(self.image_store._images[0].uuid)
        self.assertEqual(self.image_store._images, [])
        self.assertIsNone(self.image_store._current_uuid)

    def test_delete_single_active_last(self) -> None:
        """Test deleting the last image, that is also the active image."""
        self.image_store._current_uuid = self.image_store._images[-1].uuid
        self.image_store.delete_images(self.image_store._images[-1].uuid)
        ground_truth = self.ground_truth_img_list[:-1]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[-1].uuid)

        self.image_store.delete_images(self.image_store._images[-1].uuid)
        ground_truth = self.ground_truth_img_list[:-2]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

        self.image_store.delete_images(self.image_store._images[0].uuid)
        self.assertEqual(self.image_store._images, [])
        self.assertIsNone(self.image_store._current_uuid)

    def test_delete_single_active_middle(self) -> None:
        """Test deleting a middle image, that is also the active image."""
        self.image_store._current_uuid = self.image_store._images[1].uuid
        self.image_store.delete_images(self.image_store._images[1].uuid)
        ground_truth = [self.ground_truth_img_list[0], self.ground_truth_img_list[2]]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[1].uuid)

    def test_delete_empty_list(self) -> None:
        """Test deleting from an empty list."""
        self.image_store.delete_images([])
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_delete_from_empty_store(self) -> None:
        """Test deleting from an empty store."""
        self.image_store = ImageStore(self.class_store, self.mock_model)
        with self.assertRaises(ValueError):
            self.image_store.delete_images(uuid4())
        self.assertEqual(self.image_store._images, [])
        self.assertIsNone(self.image_store._current_uuid)

    def test_delete_all(self) -> None:
        """Test deleting all images."""
        self.image_store.delete_images([img.uuid for img in self.image_store._images])
        self.assertEqual(self.image_store._images, [])
        self.assertIsNone(self.image_store._current_uuid)

    def test_duplicate_uuids(self) -> None:
        """Test deleting with duplicate UUIDs."""
        with self.assertRaises(ValueError):
            self.image_store.delete_images(
                [self.image_store._images[0].uuid, self.image_store._images[0].uuid]
            )

    def test_delete_multiple_not_active(self) -> None:
        """Test deleting multiple images that are not active."""
        self.image_store.delete_images([img.uuid for img in self.image_store._images[1:]])
        ground_truth = [self.ground_truth_img_list[0]]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_delete_multiple_active_first(self) -> None:
        """Test deleting multiple images, where the first image is active."""
        self.image_store.delete_images([img.uuid for img in self.image_store._images[:2]])
        ground_truth = [self.ground_truth_img_list[2]]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_delete_multiple_active_last(self) -> None:
        """Test deleting multiple images, where the last image is active."""
        self.image_store._current_uuid = self.image_store._images[-1].uuid
        self.image_store.delete_images([img.uuid for img in self.image_store._images[-2:]])
        ground_truth = [self.ground_truth_img_list[0]]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_delete_multiple_active_middle(self) -> None:
        """Test deleting multiple images, where a middle image is active."""
        self.image_store._current_uuid = self.image_store._images[1].uuid
        self.image_store.delete_images([img.uuid for img in self.image_store._images[:2]])
        ground_truth = [self.ground_truth_img_list[2]]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

        self.setUp()
        self.image_store._current_uuid = self.image_store._images[1].uuid
        self.image_store.delete_images([img.uuid for img in self.image_store._images[1:]])
        ground_truth = [self.ground_truth_img_list[0]]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_delete_not_consecutive(self) -> None:
        """Test deleting multiple images that are not consecutive."""
        self.image_store.add_images(_cast(self.additional_image_paths))
        base_ground_truth = self.ground_truth_img_list + self.additional_images

        self.image_store.delete_images([self.image_store._images[1].uuid, self.image_store._images[3].uuid])
        ground_truth = [base_ground_truth[0], base_ground_truth[2]] + base_ground_truth[4:]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

        self.image_store.delete_images([self.image_store._images[0].uuid, self.image_store._images[2].uuid])
        ground_truth = [base_ground_truth[2]] + base_ground_truth[4:]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

        self.setUp()
        self.image_store.add_images(_cast(self.additional_image_paths))
        base_ground_truth = self.ground_truth_img_list + self.additional_images
        self.image_store._current_uuid = self.image_store._images[2].uuid
        self.image_store.delete_images([self.image_store._images[0].uuid, self.image_store._images[2].uuid])
        ground_truth = [base_ground_truth[1]] + base_ground_truth[3:]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[1].uuid)

        self.image_store.delete_images([self.image_store._images[1].uuid, self.image_store._images[2].uuid])
        ground_truth = base_ground_truth[5:]
        self._check_img_lists_equal(self.image_store._images, ground_truth)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

        self.image_store.delete_images([self.image_store._images[0].uuid])
        self.assertEqual(self.image_store._images, [])
        self.assertIsNone(self.image_store._current_uuid)

    def test_change_image_annotation_invalid(self) -> None:
        """Test changing a bounding box with an invalid index."""
        with self.assertRaises(ValueError):
            self.image_store.change_image_annotation(uuid4(), 0, [0.1, 0.1, 0.2])

    def test_change_image_annotation_no_change(self) -> None:
        """Test changing a bounding box without providing new values."""
        with self.assertRaises(Warning):
            self.image_store.change_image_annotation(self.image_store._images[0].uuid, 0)

    def test_change_image_annotation(self) -> None:
        """Test changing a bounding box."""
        self.image_store.change_image_annotation(self.image_store._images[0].uuid, 0, [0.1, 0.1, 0.2, 0.2], 1)
        self.ground_truth_img_list[0].init(self.mock_model)
        self.ground_truth_img_list[0].change_box(0, [0.1, 0.1, 0.2, 0.2])
        self.ground_truth_img_list[0].change_label(0, 1)
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)

        self.image_store.jump_to(self.image_store._images[2].uuid)
        self.image_store.change_image_annotation(self.image_store._images[2].uuid, 2, [0.0, 0.3, 0.8, 0.4])
        self.ground_truth_img_list[2].init(self.mock_model)
        self.ground_truth_img_list[2].change_box(2, [0.0, 0.3, 0.8, 0.4])
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)

        self.image_store.jump_to(self.image_store._images[1].uuid)
        self.image_store.change_image_annotation(self.image_store._images[1].uuid, 2, new_label_uid=0)
        self.ground_truth_img_list[1].init(self.mock_model)
        self.ground_truth_img_list[1].change_label(2, 0)
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)

    def test_activate_image(self) -> None:
        """Test activating an image."""
        self.image_store.activate_image(self.image_store._images[1].uuid)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[1].uuid)
        self.image_store.activate_image(self.image_store._images[0].uuid)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_activate_invalid_uuid(self) -> None:
        """Test activating an invalid UUID."""
        with self.assertRaises(ValueError):
            self.image_store.activate_image(uuid4())

    def test_next_img(self) -> None:
        """Test moving to the next image."""
        self.image_store.next()
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[1].uuid)
        self.assertTrue(self.image_store._images[1].auto_intialized)
        self.image_store.next()
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[2].uuid)
        self.assertTrue(self.image_store._images[2].auto_intialized)
        self.image_store.next()
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[2].uuid)

    def test_next_img_no_images(self) -> None:
        """Test moving to the next image when there are no images."""
        self.image_store = ImageStore(self.class_store, self.mock_model)
        self.image_store.next()
        self.assertIsNone(self.image_store._current_uuid)

    def test_next_img_uuid_none_list_not_empty(self) -> None:
        """Test moving to the next image when the current UUID is None but the list is not empty."""
        self.image_store._current_uuid = None
        self.image_store.next()
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_jump_to_invalid(self) -> None:
        """Test jumping to an invalid image."""
        with self.assertRaises(ValueError):
            self.image_store.jump_to(uuid4())

    def test_jump_to(self) -> None:
        """Test jumping to an image."""
        self.image_store.jump_to(self.image_store._images[1].uuid)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[1].uuid)
        self.assertTrue(self.image_store._images[1].auto_intialized)
        self.image_store.jump_to(self.image_store._images[0].uuid)
        self.assertEqual(self.image_store._current_uuid, self.image_store._images[0].uuid)

    def test_remove_label_replace(self) -> None:
        """Test removing a label and replacing it with another from all bounding boxes."""
        for img in self.image_store._images:
            img.init(self.mock_model)

        self.image_store.remove_label(0, 1)
        for i in range(len(self.ground_truth_img_list)):
            self.ground_truth_img_list[i].init(self.mock_model)
            self.ground_truth_img_list[i].label_uids = [2, 1, 1, 2]
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)

        self.image_store.remove_label(2, 0)
        for i in range(len(self.ground_truth_img_list)):
            self.ground_truth_img_list[i].label_uids = [0, 1, 1, 0]
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)

    def test_remove_label_remove(self) -> None:
        """Test removing a label from all bounding boxes."""
        for img in self.image_store._images:
            img.init(self.mock_model)

        self.image_store.remove_label(0)
        for i in range(len(self.ground_truth_img_list)):
            self.ground_truth_img_list[i].init(self.mock_model)
            self.ground_truth_img_list[i].label_uids = [2, 1, 2]
            self.ground_truth_img_list[i].boxes = [
                self.ground_truth_img_list[i].boxes[0]
            ] + self.ground_truth_img_list[i].boxes[2:]
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)

        self.image_store.remove_label(2)
        for i in range(len(self.ground_truth_img_list)):
            self.ground_truth_img_list[i].label_uids = [1]
            self.ground_truth_img_list[i].boxes = [self.ground_truth_img_list[i].boxes[1]]
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)

        self.image_store.remove_label(1)
        for i in range(len(self.ground_truth_img_list)):
            self.ground_truth_img_list[i].label_uids = []
            self.ground_truth_img_list[i].boxes = []
        self._check_img_lists_equal(self.image_store._images, self.ground_truth_img_list)

    def test_active_uid(self) -> None:
        """Test getting the active image's UUID."""
        self.assertEqual(self.image_store.active_uuid, self.image_store._images[0].uuid)
        self.image_store._current_uuid = self.image_store._images[1].uuid
        self.assertEqual(self.image_store.active_uuid, self.image_store._images[1].uuid)

    def test_get_img_names(self) -> None:
        """Test getting the image names."""
        self.assertEqual(self.image_store.image_names, self.image_names)
        self.image_store.add_images(_cast(self.additional_image_paths))
        self.assertEqual(self.image_store.image_names, self.image_names + self.additional_image_names)
        self.image_store = ImageStore(self.class_store, self.mock_model)
        self.assertEqual(self.image_store.image_names, [])

    def test_to_json(self) -> None:
        """Test converting the image store to a JSON serializable format."""
        self.assertEqual(self.image_store.to_json(), [img.to_dict() for img in self.ground_truth_img_list])

    def test_get_item(self) -> None:
        """Test getting an image by UUID."""
        for img in self.image_store._images:
            self.assertEqual(self.image_store[img.uuid], img)

    def test_get_item_invalid(self) -> None:
        """Test getting an image by an invalid UUID."""
        with self.assertRaises(ValueError):
            self.image_store[uuid4()]

    def test_len(self) -> None:
        """Test getting the number of images."""
        self.assertEqual(len(self.image_store), len(self.image_store._images))
        self.image_store.add_images(_cast(self.additional_image_paths))
        self.assertEqual(len(self.image_store), len(self.image_store._images))

    def test_iter(self) -> None:
        """Test iterating over the images."""
        imgs = [img for img in self.image_store]
        self._check_img_lists_equal(imgs, self.ground_truth_img_list)
