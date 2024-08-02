"""Module for testing the controller."""

import unittest
from unittest.mock import MagicMock, patch

from annotator.controller import Controller

from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage
from annotator.model.base_model import DetectionModel
from annotator.annotation_ui import ImageAnnotationGUI


class TestController(unittest.TestCase):

    @patch('annotator.controller.ImageStore')
    @patch('annotator.controller.ClassesStore')
    @patch('annotator.controller.ImageAnnotationGUI')
    def test_add_box(self, MockUI, MockClassesStore, MockImageStore):
        # Arrange
        mock_ui_instance = MockUI.return_value
        mock_img_store_instance = MockImageStore.return_value
        mock_img_store_instance.active_image.add_box = MagicMock()

        detection_model = MagicMock(spec=DetectionModel)
        controller = Controller([], detection_model)
        controller.set_view(mock_ui_instance)

        box = {'x': 10, 'y': 20, 'width': 50, 'height': 50}
        label_uid = 1

        # Act
        controller.add_box(box, label_uid)

        # Assert
        mock_img_store_instance.active_image.add_box.assert_called_once_with(box, label_uid)
        mock_ui_instance.redraw_content.assert_called_once()
        mock_ui_instance.refresh_right_sidebar.assert_called_once()