"""Module for testing the controller."""

import unittest
from unittest.mock import Mock, create_autospec, patch
from uuid import UUID

from annotator.annotation_ui import ImageAnnotationGUI
from annotator.controller import Controller
from annotator.model.base_model import DetectionModel
from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage


class TestController(unittest.TestCase):
    """Test the Controller class."""

    def setUp(self):
        """Set up the test case."""
        # Create mock instances of the required components
        self.mock_classes_store = create_autospec(ClassesStore)
        self.mock_detection_model = create_autospec(DetectionModel)
        self.mock_image_store = create_autospec(ImageStore)
        self.mock_ui = create_autospec(ImageAnnotationGUI)
        self.mock_single_image = create_autospec(SingleImage)

        # Patch the ImageStore to return a mock
        with patch("annotator.controller.ImageStore", return_value=self.mock_image_store):
            self.controller = Controller(
                classes=self.mock_classes_store,
                detection_model=self.mock_detection_model,
                initial_images=[self.mock_single_image],
            )

        # Set the view for the controller
        self.controller.set_view(self.mock_ui)
        self.assertEqual(self.controller._view, self.mock_ui)

        # Mock active_image in ImageStore
        self.controller._img_store.active_image = self.mock_single_image  # type: ignore

    def test_classes_store(self):
        """Test the classes store method is returning the correct object."""
        result = self.controller.classes_store()
        self.assertEqual(result, self.controller._class_store)

    def test_image_store(self):
        """Test the image store method is returning the correct object."""
        result = self.controller.image_store()
        self.assertEqual(result, self.controller._img_store)

    def test_active_uuid(self):
        """Test the active_uuid method is returning the correct value."""
        mock_uuid = "some-uuid-value"
        self.controller._img_store.active_uuid = mock_uuid  # type: ignore
        result = self.controller.active_uuid()
        self.assertEqual(result, mock_uuid)

    def test_add_box(self):
        """Test the add_box method is calling the correct methods."""
        # Prepare test data
        test_box = {"x": 10, "y": 10, "width": 100, "height": 50}
        test_label_uid = 1

        # Call the method under test
        self.controller.add_box(test_box, test_label_uid)

        # Verify that add_box was called on the active image with correct parameters
        self.mock_single_image.add_box.assert_called_once_with(test_box, test_label_uid)

        # Verify that redraw_content and refresh_right_sidebar are called
        self.mock_ui.redraw_content.assert_called_once()
        self.mock_ui.refresh_right_sidebar.assert_called_once()

    def test_add_box_no_redraw(self):
        """Test the add_box method is calling the correct methods when redraw=False."""
        # Prepare test data
        test_box = {"x": 10, "y": 10, "width": 100, "height": 50}
        test_label_uid = 1

        # Call the method under test with redraw=False
        self.controller.add_box(test_box, test_label_uid, redraw=False)

        # Verify that add_box was called on the active image with correct parameters
        self.mock_single_image.add_box.assert_called_once_with(test_box, test_label_uid)

        # Verify that redraw_content was not called but refresh_right_sidebar was
        self.mock_ui.redraw_content.assert_not_called()
        self.mock_ui.refresh_right_sidebar.assert_called_once()

    def test_image_names(self):
        """Test the image_names method is returning the correct value."""
        expected_names = ["image1.jpg", "image2.png"]
        self.mock_image_store.image_names = expected_names
        result = self.controller.image_names()
        self.assertEqual(result, expected_names)

    def test_current(self):
        """Test the current method is returning the correct value."""
        self.mock_image_store.active_image = self.mock_single_image
        result = self.controller.current()
        self.assertEqual(result, self.mock_single_image)

    def test_is_ready(self):
        """Test the is_ready method is returning the correct value."""
        mock_uuid = UUID("12345678123456781234567812345678")
        self.mock_image_store.__getitem__.return_value.ready = True
        result = self.controller.is_ready(mock_uuid)
        self.mock_image_store.__getitem__.assert_called_once_with(mock_uuid)
        self.assertTrue(result)

    def test_mark_ready(self):
        """Test the mark_ready method is calling the correct methods."""
        mock_uuid = UUID("12345678123456781234567812345678")
        self.controller.active_uuid = Mock(return_value=mock_uuid)  # type: ignore
        self.controller.mark_ready()
        self.mock_image_store.activate_image.assert_called_once_with(mock_uuid)
        self.mock_ui.refresh_left_sidebar.assert_called_once()

    def test_next(self):
        """Test the next method is calling the correct methods."""
        self.controller.next()
        self.mock_image_store.next.assert_called_once()
        self.mock_ui.refresh_all.assert_called_once()

    def test_jump_to(self):
        """Test the jump_to method is calling the correct methods."""
        mock_uuid = UUID("12345678123456781234567812345678")
        self.controller.jump_to(mock_uuid)
        self.mock_image_store.jump_to.assert_called_once_with(mock_uuid)
        self.mock_ui.refresh_all.assert_called_once()

    def test_add_images(self):
        """Test the add_images method is calling the correct methods."""
        test_paths = ["image1.jpg", "image2.png"]
        mock_uuids = [UUID("12345678123456781234567812345678"), UUID("87654321876543218765432187654321")]
        self.mock_image_store.add_images.return_value = mock_uuids
        result = self.controller.add_images(test_paths)
        self.mock_image_store.add_images.assert_called_once_with(test_paths)
        self.mock_ui.refresh_all.assert_called_once()
        self.assertEqual(result, mock_uuids)

    def test_delete_image(self):
        """Test the delete_image method is calling the correct methods."""
        mock_uuid = UUID("12345678123456781234567812345678")
        self.controller.active_uuid = Mock(return_value=mock_uuid)  # type: ignore
        self.controller.delete_image()
        self.mock_image_store.delete_images.assert_called_once_with(mock_uuid)
        self.mock_ui.refresh_all.assert_called_once()

    def test_export(self):
        """Test the export method is calling the correct methods."""
        path = "output.json"
        format = "json"
        ready_only = True
        test_split = 0.2

        with patch("annotator.controller.export") as mock_export:
            self.controller.export(path, format, ready_only, test_split)  # type: ignore
            mock_export.assert_called_once_with(
                path, format, self.mock_image_store, self.mock_classes_store, ready_only, test_split
            )

    def test_available_labels(self):
        """Test the available_labels method is returning the correct value."""
        mock_labels = ["label1", "label2", "label3"]
        self.mock_classes_store.get_class_names.return_value = mock_labels
        result = self.controller.available_labels()
        self.mock_classes_store.get_class_names.assert_called_once()
        self.assertEqual(result, mock_labels)

    def test_available_class_uids(self):
        """Test the available_class_uids method is returning the correct value."""
        mock_uids = [1, 2, 3]
        self.mock_classes_store.get_class_uids.return_value = mock_uids
        result = self.controller.available_class_uids()
        self.mock_classes_store.get_class_uids.assert_called_once()
        self.assertEqual(result, mock_uids)

    def test_change_image_annotation(self):
        """Test the change_image_annotation method is calling the correct methods."""
        mock_uuid = UUID("12345678123456781234567812345678")
        self.controller.active_uuid = Mock(return_value=mock_uuid)  # type: ignore
        idx = 0
        box = [10.0, 20.0, 30.0, 40.0]
        label_uid = 1
        self.controller.change_image_annotation(idx, box, label_uid)
        self.mock_image_store.change_image_annotation.assert_called_once_with(mock_uuid, idx, box, label_uid)
        self.mock_ui.redraw_content.assert_called_once_with(only_boxes=True)

    def test_change_image_annotation_no_redraw(self):
        """Test the change_image_annotation method is calling the correct methods when redraw=False."""
        mock_uuid = UUID("12345678123456781234567812345678")
        self.controller.active_uuid = Mock(return_value=mock_uuid)  # type: ignore
        idx = 0
        box = [10.0, 20.0, 30.0, 40.0]
        label_uid = 1
        self.controller.change_image_annotation(idx, box, label_uid, redraw=False)
        self.mock_image_store.change_image_annotation.assert_called_once_with(mock_uuid, idx, box, label_uid)
        self.mock_ui.redraw_content.assert_not_called()

    def test_delete(self):
        """Test the delete method is calling the correct methods."""
        self.controller._img_store.active_image = self.mock_single_image  # type: ignore
        idx = 0
        self.controller.delete(idx)
        self.mock_single_image.delete_box.assert_called_once_with(idx)
        self.mock_ui.redraw_content.assert_called_once_with(only_boxes=True)

    def test_class_iter(self):
        """Test the class_iter method is returning the correct value."""
        mock_classes = ["class1", "class2", "class3"]
        self.mock_classes_store.__iter__.return_value = iter(mock_classes)
        result = list(self.controller.class_iter())
        self.assertEqual(result, mock_classes)

    def test_delete_class(self):
        """Test the delete_class method is calling the correct methods."""
        uid = 1
        change_classes_uid = 2
        self.controller.delete_class(uid, change_classes_uid)
        self.mock_image_store.remove_label.assert_called_once_with(uid, change_classes_uid)
        self.mock_classes_store.delete_class.assert_called_once_with(uid)
        self.mock_ui.redraw_content.assert_called_once_with(only_boxes=True)

    def test_delete_class_no_redraw(self):
        """Test the delete_class method is calling the correct methods when redraw=False."""
        uid = 1
        change_classes_uid = 2
        self.controller.delete_class(uid, change_classes_uid, redraw=False)
        self.mock_image_store.remove_label.assert_called_once_with(uid, change_classes_uid)
        self.mock_classes_store.delete_class.assert_called_once_with(uid)
        self.mock_ui.redraw_content.assert_not_called()

    def test_set_default_class_uid(self):
        """Test the set_default_class_uid method is calling the correct methods."""
        uid = 1
        self.controller.set_default_class_uid(uid)
        self.mock_classes_store.set_default_uid.assert_called_once_with(uid)

    def test_get_default_class_uid(self):
        """Test the get_default_class_uid method is returning the correct value."""
        mock_default_uid = 1
        self.mock_classes_store.get_default_uid.return_value = mock_default_uid
        result = self.controller.get_default_class_uid()
        self.mock_classes_store.get_default_uid.assert_called_once()
        self.assertEqual(result, mock_default_uid)

    def test_add_new_init_class(self):
        """Test the add_new_init_class method is calling the correct methods."""
        mock_uid = 1
        mock_class_name = "new_class"
        mock_color = "#FFFFFF"
        mock_new_class = {
            "uid": mock_uid,
            "name": mock_class_name,
            "color": mock_color,
            "is_protected": False,
        }
        self.mock_classes_store.get_next_uid.return_value = mock_uid
        self.mock_classes_store.get_next_class_name.return_value = mock_class_name
        self.mock_classes_store.get_next_color.return_value = mock_color
        self.mock_classes_store.add_class.return_value = mock_new_class

        result = self.controller.add_new_init_class()

        self.mock_classes_store.get_next_uid.assert_called_once()
        self.mock_classes_store.get_next_class_name.assert_called_once()
        self.mock_classes_store.get_next_color.assert_called_once()
        self.mock_classes_store.add_class.assert_called_once_with(
            mock_uid, mock_class_name, mock_color, False
        )

        self.assertEqual(result, mock_new_class)

    def test_get_number_classes(self):
        """Test the get_number_classes method is returning the correct value."""
        mock_num_classes = 5
        self.mock_classes_store.__len__.return_value = mock_num_classes
        result = self.controller.get_number_classes()
        self.mock_classes_store.__len__.assert_called_once()
        self.assertEqual(result, mock_num_classes)

    def test_change_class_color(self):
        """Test the change_class_color method is calling the correct methods."""
        uid = 1
        new_color = "#FF0000"
        self.controller.change_class_color(uid, new_color)
        self.mock_classes_store.change_color.assert_called_once_with(uid, new_color)
        self.mock_ui.redraw_content.assert_called_once_with(only_boxes=True)

    def test_change_class_name(self):
        """Test the change_class_name method is calling the correct methods."""
        uid = 1
        new_name = "New Class Name"
        self.controller.change_class_name(uid, new_name)
        self.mock_classes_store.change_name.assert_called_once_with(uid, new_name)
        self.mock_ui.redraw_content.assert_called_once_with(only_boxes=True)
        self.mock_ui.refresh_right_sidebar.assert_called_once()

    def test_change_class_name_multiple(self):
        """Test the change_class_name method is calling the correct methods when multiple uids are given."""
        uids = [1, 2]
        new_names = ["Class1 New Name", "Class2 New Name"]
        self.controller.change_class_name(uids, new_names)
        self.mock_classes_store.change_name.assert_called_once_with(uids, new_names)
        self.mock_ui.redraw_content.assert_called_once_with(only_boxes=True)
        self.mock_ui.refresh_right_sidebar.assert_called_once()

    def test_get_class_color(self):
        """Test the get_class_color method is returning the correct value."""
        uid = 1
        mock_color = "#00FF00"
        self.mock_classes_store.get_color.return_value = mock_color
        result = self.controller.get_class_color(uid)
        self.mock_classes_store.get_color.assert_called_once_with(uid)
        self.assertEqual(result, mock_color)

    def test_get_class_name(self):
        """Test the get_class_name method is returning the correct value."""
        uid = 1
        mock_name = "Class Name"
        self.mock_classes_store.get_name.return_value = mock_name
        result = self.controller.get_class_name(uid)
        self.mock_classes_store.get_name.assert_called_once_with(uid)
        self.assertEqual(result, mock_name)

    def test_get_class_uid(self):
        """Test the get_class_uid method is returning the correct value."""
        name = "Class Name"
        mock_uid = 1
        self.mock_classes_store.get_uid.return_value = mock_uid
        result = self.controller.get_class_uid(name)
        self.mock_classes_store.get_uid.assert_called_once_with(name)
        self.assertEqual(result, mock_uid)
