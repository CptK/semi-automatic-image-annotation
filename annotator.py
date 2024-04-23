"""This module provides a simple tool for semi-automated image annotation using YOLO."""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from ultralytics import YOLO
import os


class ImageAnnotationTool:
    """A simple tool for semi-automated image annotation using YOLO.
    
    This tool allows you to annotate images with bounding boxes and class labels. Given a directory of images,
    the tool will display the images one by one and allow you to draw bounding boxes around objects in the
    image. Also, each image is processed by a YOLO model to provide initial bounding box suggestions. Labels
    for each bounding box can be selected from a dropdown menu. The annotations are saved in YOLO format once
    all images are processed. If an image should be ignored, it can be skipped.

    All images are re-saved in the specified size and format as train data. For validation, the config points
    to the same data that is used for training.
    
    For now, it is not possible to edit bounding boxes after they are drawn. You can only delete them and draw
    a new one. Also, the tool does not support multi-class annotations for a single bounding box. Moreover,
    the tool only saves the annotations once all images are processed. It is not possible to save annotations
    for a single image and continue later. Only the YOLO-style save format is supported.
    
    Args:
        master: The Tkinter root window.
        image_path: Path to the directory containing the images to annotate.
        classes: A list of class names for the objects to detect.
        save_path: Path to the directory where the annotations should be saved.
        img_size: The size to which the images should be resized for processing by the YOLO model.
        yolo_model: The YOLO model to use for object detection. Default is 'yolov8m.pt'.

    Example:
        >>> classes = ["buoy", "boat"]
        >>> root = tk.Tk()
        >>> tool = ImageAnnotationTool(
        ...     root,
        ...     "path/to/images",
        ...     classes,
        ...     save_path="annotations",
        ... )
        >>> tool.process_images()
        >>> root.mainloop()
    """
    def __init__(
        self,
        master: tk.Tk,
        image_path: str,
        classes: list[str],
        save_path: str,
        img_size: tuple[int, int] = (640, 640),
        yolo_model: str = "yolov8m.pt"
    ):
        self.master = master
        self.classes = classes
        self.image_path = image_path
        self.image_size = img_size
        self.model = YOLO(yolo_model)
        self.image_generator = self.next_image()  # Prepare the image generator
        self.save_path = save_path

        self.dataset = []
        self.skipped_images = []

        self._setup_gui()

    def _detect_single(self, img):
        """Detect objects in a single image and return the results as a list of dictionaries.
        
        Args:
            img: The image to process.
            
        Returns:
            A list of dictionaries, each containing the keys 'box' for the bounding box coordinates, 'boxn'
            for the normalized bounding box coordinates, 'label' for the class label, and 'confidence' for the
            detection confidence.
        """
        results = self.model(img)[0]
        labels = results.names
        boxes = results.boxes
        res = []
        for box in boxes:
            res.append(
                {
                    "box": box.xyxy[0].tolist(),
                    "boxn": box.xyxyn[0].tolist(),
                    "label": labels[box.cls.item()],
                    "confidence": box.conf.item(),
                }
            )
        return res

    def next_image(self):
        """A generator that yields the next image to process.

        Yields:
            A tuple containing the PIL image object, a list of bounding boxes, and the image file name.
        """
        files = [f for f in os.listdir(self.image_path) if f.lower().endswith(("png", "jpg", "jpeg"))]
        for file in files:
            try:
                img_path = os.path.join(self.image_path, file)
                img = Image.open(img_path).resize(self.image_size)
                boxes = self._detect_single(img)
                yield img, boxes, file
            except IOError as e:
                print(f"Error opening or processing {file}: {e}")

    def _setup_gui(self):
        """Set up the GUI layout and control buttons."""
        self.canvas = tk.Canvas(self.master, width=self.image_size[0], height=self.image_size[1])
        self.canvas.pack(side=tk.LEFT)

        self.sidebar = tk.Frame(self.master, padx=5, pady=5)
        self.sidebar.pack(fill=tk.BOTH, side=tk.RIGHT, expand=True)

        # Place control buttons once
        tk.Button(self.sidebar, text="Skip", command=self._skip_image).pack(side=tk.TOP)
        tk.Button(self.sidebar, text="Save", command=self._save_annotations).pack(side=tk.TOP)

        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.current_box = None
        self.start_x = None
        self.start_y = None

    def process_images(self):
        """Process the next image in the generator and display it in the GUI."""
        try:
            self.img, self.boxes, self.file = next(self.image_generator)
            self.tk_image = ImageTk.PhotoImage(self.img)
            self._refresh_canvas()
            self._refresh_sidebar()
        except StopIteration:
            print("No more images to process")
            self.save_yolo_style()
            exit()

    def save_yolo_style(self):
        """Save the annotations in YOLO format.
        
        Creates the following files:
        - A directory structure for the YOLO dataset
        - A data.yaml file containing the dataset configuration
        - Image files in the train/images directory
        - Label files in the train/labels directory
        """
        os.mkdir(self.save_path)
        os.mkdir(os.path.join(self.save_path, "train"))

        img_path = os.path.join(self.save_path, "train", "images")
        os.mkdir(img_path)
        label_path = os.path.join(self.save_path, "train", "labels")
        os.mkdir(label_path)

        with open(os.path.join(self.save_path, "data.yaml"), "w") as f:
            f.write(f"train: ../{self.save_path}/train\n")
            f.write(f"val: ../{self.save_path}/train\n")
            f.write(f"nc: {len(self.classes)}\n")
            f.write("names: " + str(self.classes))

        for idx, data in enumerate(self.dataset):
            img = data["img"]
            img.save(os.path.join(img_path, f"img_{idx}.jpg"))
            with open(os.path.join(label_path, f"img_{idx}.txt"), "w") as f:
                for box in data["boxes"]:
                    x1, y1, x2, y2 = box["boxn"]
                    label = self.classes.index(box["label"])
                    f.write(f"{label} {x1} {y1} {x2} {y2}\n")

    def _refresh_canvas(self):
        """Clear the canvas and redraw the image and bounding boxes."""
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        for box in self.boxes:
            x1, y1, x2, y2 = box["box"]
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red")
            self.canvas.create_text(x1, y1 - 10, text=f"{box['label']}", fill="red", font="Arial 14")

    def _refresh_sidebar(self):
        """Refresh the sidebar with the current bounding boxes."""
        # Clear existing content in the sidebar (except the control buttons)
        for widget in self.sidebar.winfo_children()[2:]:  # Assuming the first two widgets are control buttons
            widget.destroy()
        for idx, box in enumerate(self.boxes):
            frame = tk.Frame(self.sidebar)
            frame.pack(fill=tk.X)
            label = ttk.Label(frame, text=f"Box {idx+1}:")
            label.pack(side=tk.LEFT)
            dropdown = ttk.Combobox(frame, values=self.classes, state="readonly")
            dropdown.set(box["label"])
            dropdown.pack(side=tk.LEFT)
            dropdown.bind("<<ComboboxSelected>>", lambda event, idx=idx: self._update_label(idx, event))
            delete_button = tk.Button(frame, text="Delete", command=lambda idx=idx: self._delete_box(idx))
            delete_button.pack(side=tk.LEFT)

    def _update_label(self, index, event):
        """Update the label of a bounding box in the list and refresh the canvas and sidebar."""
        new_label = event.widget.get()
        self.boxes[index]["label"] = new_label
        self._refresh_canvas()

    def _delete_box(self, index):
        """Delete a bounding box from the list and refresh the canvas and sidebar."""
        del self.boxes[index]
        self._refresh_canvas()
        self._refresh_sidebar()

    def _skip_image(self):
        """Skip the current image and move on to the next one."""
        self.skipped_images.append(self.file)
        self.process_images()

    def _save_annotations(self):
        """Save the current annotations and move on to the next image."""
        self.dataset.append({"img": self.img, "boxes": self.boxes})
        self.process_images()

    def _on_mouse_down(self, event):
        """Start drawing a new bounding box when the mouse is clicked."""
        # Start drawing a new bounding box
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_box = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="red"
        )

    def _on_mouse_move(self, event):
        """Adjust the bounding box while moving the mouse."""
        # Adjust the bounding box while moving the mouse
        curX, curY = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.coords(self.current_box, self.start_x, self.start_y, curX, curY)

    def _on_mouse_up(self, event):
        """Finalize the bounding box when the mouse is released."""
        # Finalize the bounding box coordinates
        x1, y1, x2, y2 = self.canvas.coords(self.current_box)
        # Normalize coordinates
        nx1, ny1, nx2, ny2 = (
            x1 / self.image_size[0],
            y1 / self.image_size[1],
            x2 / self.image_size[0],
            y2 / self.image_size[1],
        )
        self.boxes.append(
            {
                "box": [x1, y1, x2, y2],
                "boxn": [nx1, ny1, nx2, ny2],
                "label": self.classes[0],  # Default label
                "confidence": 1.0,  # Default confidence
            }
        )
        self._refresh_sidebar()


if __name__ == "__main__":
    IMG_DIR = "path/to/images"
    classes = ["cat", "dog"]
    root = tk.Tk()
    tool = ImageAnnotationTool(
        root,
        IMG_DIR,
        classes,
        save_path="Results",
    )
    tool.process_images()
    root.mainloop()
