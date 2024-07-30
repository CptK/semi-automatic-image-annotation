"""Thid module contains functions for exporting annotations to different formats."""

import json
import os
import random
from io import TextIOWrapper
from typing import Literal

import yaml
from PIL import Image

from annotator.store.classes_store import ClassesStore
from annotator.store.image_store import ImageStore
from annotator.store.single_image import SingleImage


def export(
    path: str,
    format: Literal["csv", "json", "yolo"],
    image_store: ImageStore,
    class_store: ClassesStore,
    only_ready: bool,
    test_split: float,
    seed: int = 42,
    **kwargs,
):
    """Export the annotations to a file in the specified format.

    Args:
        path: The path to the output file or directory.
        format: The format in which to export the annotations (csv, json, or yolo).
        image_store: The image store containing the annotations.
        class_store: The class store containing the class labels.
        only_ready: If True, only export images that have been marked as ready.
        test_split: The fraction of the data to use for testing.
        seed: The random seed to use for splitting the data.
    """
    data = [a for a in image_store if not only_ready or a.ready]

    random.seed(seed)
    random.shuffle(data)

    train = data[: int(len(data) * (1 - test_split))]
    test = data[int(len(data) * (1 - test_split)) :]

    match format.lower():
        case "csv":
            _export_csv(path, train, test, class_store, **kwargs)
        case "json":
            _export_json(path, train, test, class_store)
        case "yolo":
            _export_yolo(path, train, test, class_store)
        case _:
            raise ValueError(f"Unsupported export format: {format}")


def _export_csv(
    path: str,
    train: list[SingleImage],
    test: list[SingleImage],
    class_store: ClassesStore,
    delimiter: str = ";",
):
    """Export the annotations to a CSV file.

    Using this format, images without annotations are not included in the output. Each row in the CSV file
    refers to one bounding box and contains the following fields:
    path, file_name, center_x, center_y, width, height, label, split.

    Args:
        path: The path to the output CSV file.
        train: The list of annotations to use for training.
        test: The list of annotations to use for testing.
        class_store: The class store containing the class labels.
        delimiter: The delimiter to use for separating fields in the CSV file.
    """
    if not path.endswith(".csv"):
        raise ValueError("Export path must be a CSV file.")

    def process(data: list[SingleImage], file: TextIOWrapper, split: Literal["train", "test"]):
        for annotation in data:
            for box, label_uid in zip(annotation.boxes, annotation.label_uids):
                label = class_store.get_name(label_uid)
                center_x, center_y, width, height = box
                file.write(
                    f"{annotation.path}{delimiter}{annotation.name}{delimiter}{center_x}{delimiter} \
                    {center_y}{delimiter}{width}{delimiter}{height}{delimiter}{label}{delimiter}{split}\n"
                )

    with open(path, "w") as f:
        f.write(
            f"path{delimiter}file_name{delimiter}center_x{delimiter}center_y{delimiter}width{delimiter}height{delimiter}label{delimiter}split\n"
        )
        process(train, f, "train")
        process(test, f, "test")


def _export_json(path: str, train: list[SingleImage], test: list[SingleImage], class_store: ClassesStore):
    """Export the annotations to a JSON file.

    Args:
        path: The path to the output JSON file.
        data: The list of annotations to export.
    """
    if not path.endswith(".json"):
        raise ValueError("Export path must be a JSON file.")

    train_json = [a.to_dict() for a in train]
    test_json = [a.to_dict() for a in test]

    output = {"class_mapping": class_store.classes, "train": train_json, "test": test_json}

    with open(path, "w") as f:
        json.dump(output, f, indent=4)


def _export_yolo(path: str, train: list[SingleImage], test: list[SingleImage], class_store: ClassesStore):
    """Export the annotations to the YOLO format.

    Args:
        path: The path to the output directory.
        train: The list of annotations to use for training.
        test: The list of annotations to use for testing.
        class_store: The class store containing the class labels.
    """
    if not os.path.exists(path):
        os.makedirs(path)

    os.makedirs(os.path.join(path, "train", "images"), exist_ok=True)
    os.makedirs(os.path.join(path, "train", "labels"), exist_ok=True)
    os.makedirs(os.path.join(path, "test", "images"), exist_ok=True)
    os.makedirs(os.path.join(path, "test", "labels"), exist_ok=True)

    _process_yolo(path, train, class_store, "train")
    _process_yolo(path, test, class_store, "test")

    # create a yaml config file
    data_yaml = {
        "train": "../train/images",
        "test": "../test/images",
        "nc": len(class_store.get_class_names()),
        "names": {i: label for i, label in enumerate(class_store.get_class_names())},
    }

    with open(os.path.join(path, "data.yaml"), "w") as f:
        yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)


def _process_yolo(path: str, raw_data: list[SingleImage], class_store: ClassesStore, split: str):
    """Process the annotations for the YOLO format.

    Args:
        path: The path to the output directory.
        raw_data: The list of annotations to process.
        class_store: The class store containing the class labels.
        split: The split to process (train or test).
    """
    for i, data in enumerate(raw_data):
        with Image.open(data.path) as img:
            img = img.resize((640, 640))
            img.save(os.path.join(path, split, "images", f"{i}.jpg"))

        with open(os.path.join(path, split, "labels", f"{i}.txt"), "w") as f:
            for box, label_uid in zip(data.boxes, data.label_uids):
                label = class_store.get_name(label_uid)
                x_center, y_center, width, height = box

                # write the label and the normalized box coordinates
                label_idx = class_store.get_class_names().index(label)
                f.write(f"{label_idx} {x_center} {y_center} {width} {height}\n")
