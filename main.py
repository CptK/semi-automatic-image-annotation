from ultralytics import YOLO

from annotator.annotation_store import AnnotationStore
from annotator.annotation_ui import ImageAnnotationGUI


def main():
    yolo_model = YOLO("yolov8m.pt")  # Load the YOLO model
    store = AnnotationStore(r"C:\Users\m-kor\OneDrive\Bilder\Buoys", yolo_model, ["none", "buoy", "boat"])
    app = ImageAnnotationGUI(store)
    app.mainloop()


if __name__ == "__main__":
    main()
