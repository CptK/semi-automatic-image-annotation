"""This module tests the `SingleImage` class."""

import os
import unittest
from uuid import UUID

from PIL import Image

from annotator.model.mock_model import MockModel
from annotator.store.classes_store import ClassesStore
from annotator.store.single_image import SingleImage


class TestSingleImage(unittest.TestCase):

    def setUp(self):
        self.img_name = "test_img_1.JPEG"
        self.img_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "images", self.img_name)
        )
        self.classes_store = ClassesStore(["none", "boat", "car"])
        self.img = SingleImage(self.img_path, self.img_name, self.classes_store)
        img = Image.open(self.img.path)
        self.img_size = img.size
        img.close()
        self.model = MockModel([[0, 0, 100, 100]], ["boat"], None, self.img_size)

    def test_init(self):
        self.assertEqual(self.img.path, self.img_path)
        self.assertEqual(self.img.name, self.img_name)
        self.assertEqual(self.img.class_store, self.classes_store)
        self.assertEqual(self.img.boxes, [])
        self.assertEqual(self.img.label_uids, [])
        self.assertFalse(self.img.ready)
        self.assertFalse(self.img.auto_intialized)
        self.assertEqual(self.img.img_size, self.img_size)
        self.assertIsNotNone(self.img.uuid)
        self.assertIsInstance(self.img.uuid, UUID)

    def test_init_auto(self):
        self.img.init(self.model)
        self.assertEqual(
            self.img.boxes,
            [[50 / self.img_size[0], 50 / self.img_size[1], 100 / self.img_size[0], 100 / self.img_size[1]]],
        )
        self.assertEqual(self.img.label_uids, [1])
        self.assertTrue(self.img.auto_intialized)
        # check that the image is not initialized again
        self.img.init(self.model)
        self.assertTrue(self.img.auto_intialized)
        # check that passing None does not raise an error
        self.img.init(None)

    def test_init_auto_fail(self):
        self.img.path = "invalid_path"
        self.img.init(self.model)
        self.assertEqual(self.img.boxes, [])
        self.assertEqual(self.img.label_uids, [])
        self.assertFalse(self.img.auto_intialized)

    def test_mark_ready(self):
        self.assertFalse(self.img.ready)
        self.img.mark_ready()
        self.assertTrue(self.img.ready)

    def test_change_label(self):
        self.img.init(self.model)
        self.assertEqual(self.img.label_uids, [1])
        self.img.change_label(0, 0)
        self.assertEqual(self.img.label_uids, [0])

    def test_add_box(self):
        self.img.add_box([0.1, 0.1, 0.2, 0.2], 1)
        self.assertEqual(self.img.boxes, [[0.1, 0.1, 0.2, 0.2]])
        self.assertEqual(self.img.label_uids, [1])
        self.img.add_box([0.3, 0.3, 0.4, 0.4], 0)
        self.assertEqual(self.img.boxes, [[0.1, 0.1, 0.2, 0.2], [0.3, 0.3, 0.4, 0.4]])
        self.assertEqual(self.img.label_uids, [1, 0])

    def test_delete_box(self):
        self.img.add_box([0.1, 0.1, 0.2, 0.2], 1)
        self.img.add_box([0.3, 0.3, 0.4, 0.4], 0)
        self.img.delete_box(0)
        self.assertEqual(self.img.boxes, [[0.3, 0.3, 0.4, 0.4]])
        self.assertEqual(self.img.label_uids, [0])
        self.img.delete_box(0)
        self.assertEqual(self.img.boxes, [])
        self.assertEqual(self.img.label_uids, [])

    def test_change_box(self):
        self.img.add_box([0.1, 0.1, 0.2, 0.2], 1)
        self.img.change_box(0, [0.3, 0.3, 0.4, 0.4])
        self.assertEqual(self.img.boxes, [[0.3, 0.3, 0.4, 0.4]])
        self.assertEqual(self.img.label_uids, [1])

    def test_change_box_invalid(self):
        self.img.add_box([0.1, 0.1, 0.2, 0.2], 1)
        with self.assertRaises(ValueError):
            self.img.change_box(0, [0.3, 0.3, 0.4])

    def test_labels_to_uids(self):
        self.assertEqual(self.img.labels_to_uids([]), [])
        self.assertEqual(self.img.labels_to_uids(["none", "boat", "none"]), [0, 1, 0])
        self.assertEqual(self.img.labels_to_uids(["none", "car", "unknown"]), [0, 2, 0])

    def test_delete_all_with_label(self):
        self.img.add_box([0.1, 0.1, 0.2, 0.2], 1)
        self.img.add_box([0.3, 0.3, 0.4, 0.4], 0)
        self.img.add_box([0.5, 0.5, 0.6, 0.6], 1)
        self.img.delete_all_with_label(1)
        self.assertEqual(self.img.boxes, [[0.3, 0.3, 0.4, 0.4]])
        self.assertEqual(self.img.label_uids, [0])

    def test_change_all_labels(self):
        self.img.add_box([0.1, 0.1, 0.2, 0.2], 1)
        self.img.add_box([0.3, 0.3, 0.4, 0.4], 0)
        self.img.add_box([0.5, 0.5, 0.6, 0.6], 1)
        self.img.add_box([0.7, 0.7, 0.8, 0.8], 2)
        self.img.change_all_labels(1, 2)
        self.assertEqual(self.img.label_uids, [2, 0, 2, 2])

    def test_uids_to_labels(self):
        self.assertEqual(self.img.uids_to_labels([]), [])
        self.assertEqual(self.img.uids_to_labels([0, 1, 0]), ["none", "boat", "none"])
        self.assertEqual(self.img.uids_to_labels([0, 2, 1]), ["none", "car", "boat"])

    def test_to_dict(self) -> None:
        """Test the to_dict method."""
        bboxes = [[0.1, 0.1, 0.2, 0.2], [0.3, 0.3, 0.4, 0.4], [0.5, 0.5, 0.6, 0.6]]
        for i, box in enumerate(bboxes):
            self.img.add_box(box, i)

        res = self.img.to_dict()
        self.assertEqual(list(res.keys()), ["file_path", "file_name", "boxes", "labels", "ready"])
        self.assertEqual(res["file_path"], self.img.path)
        self.assertEqual(res["file_name"], self.img.name)
        self.assertEqual(res["boxes"], bboxes)
        self.assertEqual(res["labels"], self.img.uids_to_labels(list(range(len(bboxes)))))
        self.assertEqual(res["ready"], self.img.ready)
