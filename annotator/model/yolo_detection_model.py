"""A class for object detection using a YOLO model."""

from PIL import Image

from annotator.model.base_model import DetectionModel


class YOLODetectionModel(DetectionModel):
    """A class for object detection using a PyTorch model.

    The ouput format of the model should be a list of dictionaries, each containing the keys
    - 'box' for the bounding box coordinates in the format [x1, y1, x2, y2],
    - 'boxn' for the normalized bounding box coordinates in the format [x1, y1, x2, y2],
    - 'label' for the class label,
    - 'confidence' for the detection confidence.

    Args:
        model: The PyTorch model to use for object detection.
        available_labels: A list of available class labels.
        input_size: The size to which to resize the input images.
    """

    def __init__(self, model, available_labels: list[str], input_size: tuple[int, int] = (640, 640)):
        self.model = model
        self.available_labels = available_labels
        self.input_size = input_size

    def __call__(self, img: Image.Image):
        """Detect objects in a single image and return the results as a list of dictionaries.

        Args:
            img: The image to process.

        Returns:
            A list of dictionaries, each containing the keys 'box' for the bounding box coordinates, 'boxn'
            for the normalized bounding box coordinates, 'label' for the class label, and 'confidence' for the
            detection confidence.
        """
        img = img.resize(self.input_size)
        results = self.model(img)[0]
        labels = results.names
        boxes = results.boxes
        res = []
        for box in boxes:
            label = labels[box.cls.item()]
            if label not in self.available_labels:
                label = "none"

            # convert [x1, y1, x2, y2] to [center_x, center_y, width, height], all normalized to [0, 1]
            boxn = box.xyxyn[0].tolist()
            boxn = [(boxn[0] + boxn[2]) / 2, (boxn[1] + boxn[3]) / 2, boxn[2] - boxn[0], boxn[3] - boxn[1]]

            res.append(
                {
                    "box": box.xyxy[0].tolist(),
                    "boxn": boxn,
                    "label": label,
                    "confidence": box.conf.item(),
                }
            )
        return res
