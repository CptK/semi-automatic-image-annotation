"""A base class for object detection models."""

from abc import ABC

from PIL import Image


class DetectionModel(ABC):
    """A base class for object detection models."""

    def __call__(self, img: Image.Image):
        """Detect objects in an image and return the results.

        Args:
            img: The image to process.

        Returns:
            A list of dictionaries, each containing the keys 'box' for the bounding box coordinates, 'boxn'
            for the normalized bounding box coordinates, 'label' for the class label, and 'confidence' for the
            detection confidence.
        """
        raise NotImplementedError