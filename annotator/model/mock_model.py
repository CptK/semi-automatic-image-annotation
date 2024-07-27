"""This module contains a mock object detection model for testing purposes."""

from PIL import Image

from annotator.model.base_model import DetectionModel


class MockModel(DetectionModel):
    """This class is a mock object detection model for testing purposes.

    It will return a fixed set of bounding boxes and labels for every image.

    Args:
        bboxes: A list of bounding boxes to return for every image. Every box should be represented as a list
            of four entries [x1, y1, x2, y2], where x1, y1 are the coordinates of the top-left corner and x2,
            y2 are the coordinates of the bottom-right corner. All values should be pixel coordinates.
        labels: A list of class labels to return for every image.
        confidences: A list of detection confidences to return for every image. If None, the confidence will
            be set to 1.
        img_size: The size to which to resize the input images.
    """

    def __init__(
        self,
        bboxes: list[list[float]],
        labels: list[str],
        confidences: list[float] | None = None,
        img_size: tuple[int, int] = (640, 640),
    ):
        self.bboxes = bboxes
        self.labels = labels
        self.confidences = confidences if confidences is not None else [1] * len(bboxes)
        self.img_size = img_size

    def __call__(self, _: Image.Image):
        res = []
        for box, label, conf in zip(self.bboxes, self.labels, self.confidences):
            box_center = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]
            box_size = [box[2] - box[0], box[3] - box[1]]
            boxn = [
                box_center[0] / self.img_size[0],
                box_center[1] / self.img_size[1],
                box_size[0] / self.img_size[0],
                box_size[1] / self.img_size[1],
            ]
            res.append(
                {
                    "box": box,
                    "boxn": boxn,
                    "label": label,
                    "confidence": conf,
                }
            )
        return res
