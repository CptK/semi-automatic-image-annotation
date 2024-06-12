from typing import Any, Literal

from annotator.annotation_store import AnnotationStore, SingleImage
from annotator.ui import UI


class Controller:

    def __init__(self, store: AnnotationStore):
        self._store = store
        self._view: UI | None = None

    def set_view(self, view: UI):
        """Set the view for the controller."""
        self._view = view

    def current_index(self) -> int:
        """The index of the *current* image in the dataset."""
        return self._store.current_index

    def current_boxes(self):
        """The bounding boxes of the *current* image."""
        return self._store.boxes

    def current_labels(self):
        """The labels of the *current* image."""
        return self._store.labels

    def add_box(self, box: Any, label: str = "none"):
        """Add a new bounding box to the *current* image."""
        self._store.add_box(box, label)
        self._view.redraw_content()  # type: ignore
        self._view.refresh_right_sidebar()  # type: ignore

    def image_names(self):
        """A list of file names of all images in the dataset."""
        return self._store.image_names

    def current(self) -> SingleImage:
        """The index of the *current* image in the dataset."""
        return self._store.current

    def current_file_path(self):
        """The absolute file path of the *current* image."""
        return self._store.file_path

    def current_image_size(self):
        """The size of the *current* image."""
        return self._store.image_size

    def ready(self):
        """Whether the *current* image has been marked as ready for export."""
        return self._store.ready

    def mark_ready(self):
        """Mark the *current* image as ready for export."""
        self._store.mark_ready()

    def next(self):
        """Move to the next image in the dataset."""
        self._store.next()
        self._view.refresh_all()  # type: ignore

    def jump_to(self, idx: int):
        """Jump to a specific image index."""
        self._store.jump_to(idx)
        self._view.refresh_all()  # type: ignore

    def export(self, path: str, format: Literal["json", "csv", "yolo"], ready_only: bool, train_split: float):
        """Export the annotations to disk."""
        self._store.export(path, format, ready_only, train_split)

    def available_labels(self):
        """The available labels for annotation."""
        return self._store.available_labels

    def change_label(self, idx: int, label: str):
        """Change the label for the given index."""
        self._store.change_label(idx, label)
        self._view.redraw_content()  # type: ignore

    def delete(self, idx: int):
        """Delete the label for the given index."""
        self._store.delete(idx)
        self._view.redraw_content()  # type: ignore

    def __len__(self) -> int:
        """The number of images in the dataset."""
        return len(self._store)

    def __getitem__(self, idx: int) -> SingleImage:
        """Get the image at the given index."""
        return self._store[idx]
