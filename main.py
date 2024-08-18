"""Main module for the annotator application."""

import os
from typing import cast

from ultralytics import YOLO

from annotator.annotation_ui import ImageAnnotationGUI
from annotator.controller import Controller
from annotator.model.yolo_detection_model import YOLODetectionModel
from annotator.store.single_image import SingleImage


def main():
    yolo_model = YOLO("yolov8m.pt")  # Load the YOLO model
    model = YOLODetectionModel(yolo_model, ["none", "buoy", "boat"])  # Create a detection model
    base_path = r"C:\Users\m-kor\OneDrive\Bilder\Buoys"
    image_paths = [os.path.join(base_path, image) for image in os.listdir(base_path)]
    controller = Controller(["none", "buoy", "boat"], model, cast(list[SingleImage | str], image_paths))
    app = ImageAnnotationGUI(controller)
    controller.set_view(app)
    app.mainloop()


if __name__ == "__main__":
    main()
