from ultralytics import YOLO

from annotator.annotation_store import AnnotationStore
from annotator.annotation_ui import ImageAnnotationGUI
from annotator.controller import Controller


def main():
    yolo_model = YOLO("yolov8m.pt")  # Load the YOLO model
    store = AnnotationStore(r"C:\Users\m-kor\OneDrive\Bilder\Buoys", yolo_model, ["none", "buoy", "boat"])
    controller = Controller(store)
    app = ImageAnnotationGUI(controller)
    controller.set_view(app)
    app.mainloop()


if __name__ == "__main__":
    main()
