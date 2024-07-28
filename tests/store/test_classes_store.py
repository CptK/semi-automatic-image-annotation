"""Module for testing the classes store module."""

import unittest
from typing import cast

from annotator.store.classes_store import ClassesStore


class TestClassesStore(unittest.TestCase):
    """Tests for the ClassesStore class."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.classes_dict = [
            {"uid": 0, "name": "class0", "color": "#FF0000", "default": True},
            {"uid": 1, "name": "class1", "color": "#00FF00", "default": False},
            {"uid": 2, "name": "class2", "color": "#0000FF", "default": False},
        ]
        self.classes_str = ["class0", "class1", "class2"]
        self.store = ClassesStore(cast(list[dict[str, str]], self.classes_dict.copy()))

    def test_init_dict(self) -> None:
        """Test initialization with a list of dictionaries."""
        store = ClassesStore(cast(list[dict[str, str]], self.classes_dict.copy()))
        self.assertEqual(store.classes, self.classes_dict)

    def test_init_str(self) -> None:
        """Test initialization with a list of strings."""
        store = ClassesStore(cast(list[dict[str, str]], self.classes_dict.copy()))
        self.assertEqual(store.classes, self.classes_dict)

    def test_init_no_default(self) -> None:
        """Test initialization with no default class."""
        classes = self.classes_dict.copy()
        classes[0]["default"] = False
        store = ClassesStore(cast(list[dict[str, str]], classes.copy()))
        self.assertTrue(store.classes[0]["default"])

    def test_init_multiple_default(self) -> None:
        """Test initialization with multiple default classes."""
        classes = self.classes_dict.copy()
        classes[0]["default"] = False
        classes[1]["default"] = True
        classes[2]["default"] = True
        store = ClassesStore(cast(list[dict[str, str]], classes.copy()))
        self.assertFalse(store.classes[0]["default"])
        self.assertTrue(store.classes[1]["default"])
        self.assertFalse(store.classes[2]["default"])

    def test_add_class_success(self) -> None:
        """Test adding a class successfully."""
        new_class = self.store.add_class(3, "class3", "#FFFF00")
        self.assertEqual(new_class, {"uid": 3, "name": "class3", "color": "#FFFF00", "default": False})

    def test_add_class_duplicate_uid(self) -> None:
        """Test adding a class with a duplicate UID."""
        with self.assertRaises(ValueError):
            self.store.add_class(0, "class3", "#FFFF00")

    def test_add_class_duplicate_name(self) -> None:
        """Test adding a class with a duplicate name."""
        with self.assertRaises(ValueError):
            self.store.add_class(3, "class0", "#FFFF00")

    def test_add_class_multiple_default(self) -> None:
        """Test adding a class with multiple default classes."""
        with self.assertRaises(ValueError):
            self.store.add_class(4, "class4", "#00FFFF", is_default=True)

    def test_delete_class_not_default(self) -> None:
        """Test deleting a class."""
        self.store.delete_class(1)
        self.assertEqual(self.store.classes, [self.classes_dict[0], self.classes_dict[2]])

    def test_delete_default_class(self) -> None:
        """Test deleting the default class."""
        self.store.delete_class(0)
        ground_truth = self.classes_dict.copy()[1:]
        ground_truth[0]["default"] = True
        self.assertEqual(self.store.classes, ground_truth)

    def test_get_class_names(self) -> None:
        """Test getting class names."""
        self.assertEqual(self.store.get_class_names(), self.classes_str)

    def test_get_class_uids(self) -> None:
        """Test getting class UIDs."""
        self.assertEqual(self.store.get_class_uids(), [cls["uid"] for cls in self.classes_dict])

    def test_get_next_color(self) -> None:
        all_colors = self.store.DEFAULT_COLORS
        self.assertEqual(self.store.get_next_color(), all_colors[3])
        for i in range(5):
            self.store.add_class(i + 4, f"class{i + 4}", all_colors[i])
            self.assertEqual(self.store.get_next_color(), all_colors[(i + 4) % len(all_colors)])

    def test_get_next_class_name(self) -> None:
        """Test getting the next class name."""
        self.assertEqual(self.store.get_next_class_name(), "Class 4")
        self.store.delete_class(0)
        self.assertEqual(self.store.get_next_class_name(), "Class 3")
        self.store.add_class(4, "Class 4", "#FFFFFF")
        self.assertEqual(self.store.get_next_class_name(), "Class 5")

    def test_get_next_uid(self) -> None:
        """Test getting the next class name."""
        self.assertEqual(self.store.get_next_uid(), 3)
        self.store.delete_class(0)
        self.store.add_class(3, "class 3", "#FFFFFF")
        self.assertEqual(self.store.get_next_uid(), 4)
        self.store.delete_class(1)
        self.store.delete_class(2)
        self.assertEqual(self.store.get_next_uid(), 4)
        for i in range(5):
            self.store.add_class(i + 4, f"class{i + 4}", "#FFFFFF")
            self.assertEqual(self.store.get_next_uid(), i + 5)

    def test_set_get_default_uid(self) -> None:
        """Test getting the default class UID."""
        self.assertEqual(self.store.get_default_uid(), 0)
        self.store.set_default_uid(1)
        self.assertEqual(self.store.get_default_uid(), 1)
        self.store.set_default_uid(2)
        self.assertEqual(self.store.get_default_uid(), 2)

    def test_get_color(self) -> None:
        """Test getting the color of a class."""
        for cls in self.classes_dict:
            self.assertEqual(self.store.get_color(cast(int, cls["uid"])), cls["color"])

    def test_get_default_class(self) -> None:
        """Test getting the default class."""
        self.assertEqual(self.store.get_default_class(), self.classes_dict[0])

    def test_change_name_single(self) -> None:
        """Test changing the name of a class."""
        self.store.change_name(0, "new_name")
        self.assertEqual(self.store.classes[0]["name"], "new_name")
        ground_truth = self.classes_dict.copy()
        ground_truth[0]["name"] = "new_name"
        self.assertEqual(self.store.classes, ground_truth)

    def test_change_name_multiple(self) -> None:
        """Test changing the name of multiple classes."""
        ids = [cast(int, cls["uid"]) for cls in self.classes_dict]
        new_names = [f"new_name{i}" for i in range(len(ids))]
        self.store.change_name(ids, new_names)
        for i, _ in enumerate(ids):
            self.assertEqual(self.store.classes[i]["name"], new_names[i])

    def test_change_duplicate_class_name(self) -> None:
        """Test changing the name to a duplicate name."""
        with self.assertRaises(ValueError):
            self.store.change_name(0, "class1")

        with self.assertRaises(ValueError):
            self.store.change_name([0, 1], ["class10", "class10"])

    def test_change_name_unequal_sizes(self) -> None:
        """Test changing the name with unequal sizes."""
        with self.assertRaises(ValueError):
            self.store.change_name([0, 1], ["class10"])

    def test_change_color(self) -> None:
        """Test changing the color of a class."""
        self.store.change_color(0, "#FFFFFF")
        ground_truth = self.classes_dict.copy()
        ground_truth[0]["color"] = "#FFFFFF"
        self.assertEqual(self.store.classes, ground_truth)
        self.store.change_color(1, "#000000")
        ground_truth[1]["color"] = "#000000"
        self.assertEqual(self.store.classes, ground_truth)

    def test_get_name(self) -> None:
        """Test getting the name of a class."""
        for cls in self.classes_dict:
            self.assertEqual(self.store.get_name(cast(int, cls["uid"])), cls["name"])

    def test_get_uid(self) -> None:
        """Test getting the UID of a class."""
        for cls in self.classes_dict:
            self.assertEqual(self.store.get_uid(cast(str, cls["name"])), cls["uid"])

    def test_get_item(self) -> None:
        """Test getting a class by its UID."""
        for i, cls in enumerate(self.classes_dict):
            self.assertEqual(self.store[i], cls)

    def test_len(self) -> None:
        """Test getting the number of classes."""
        self.assertEqual(len(self.store), len(self.classes_dict))
        self.store.add_class(3, "class3", "#FFFFFF")
        self.assertEqual(len(self.store), len(self.classes_dict) + 1)
        self.store.delete_class(0)
        self.store.delete_class(1)
        self.assertEqual(len(self.store), len(self.classes_dict) - 1)

    def test_iter(self) -> None:
        """Test iterating over the classes."""
        for i, cls in enumerate(self.store):
            self.assertEqual(cls, self.classes_dict[i])
