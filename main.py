"""Main module for the annotator application."""

import os

from ultralytics import YOLO

from annotator.annotation_ui import ImageAnnotationGUI
from annotator.controller import Controller
from annotator.store.annotation_store import AnnotationStore


def main():
    yolo_model = YOLO("yolov8m.pt")  # Load the YOLO model
    base_path = r"C:\Users\m-kor\OneDrive\Bilder\Buoys"
    image_paths = [os.path.join(base_path, image) for image in os.listdir(base_path)]
    store = AnnotationStore(image_paths, yolo_model, ["none", "buoy", "boat"])
    controller = Controller(store)
    app = ImageAnnotationGUI(controller)
    controller.set_view(app)
    app.mainloop()


if __name__ == "__main__":
    main()
