"""Module for testing the annotation export functionality."""

import json
import os
import random
import tempfile
from abc import ABC

import numpy as np
import pandas as pd
import yaml
from PIL import Image

from annotator.store.annotation_export import export
from annotator.store.single_image import SingleImage
from tests.store.base_environment import TestEnvironment


class TestExportBase(TestEnvironment, ABC):
    """Base class for testing the export functionality."""

    def __init__(self, file_name: str, *args, **kwargs) -> None:
        """Initialize the test case."""
        super().__init__(*args, **kwargs)
        self.file_name = file_name

    def setUp(self) -> None:
        """Set up the test case."""
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, self.file_name)

    def tearDown(self) -> None:
        """Tear down the test case."""
        self.temp_dir.cleanup()


class TestInvalidExport(TestExportBase):
    """Class for testing invalid export formats."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the test case."""
        super().__init__("test", *args, **kwargs)

    def test_invalid_format(self) -> None:
        """Test exporting annotations to an invalid format."""
        with self.assertRaises(ValueError):
            export(self.temp_file, "invalid_format", self.image_store, self.class_store, True, 0.0)  # type: ignore


class TestExportCSV(TestExportBase):
    """Class for testing the CSV export functionality."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the test case."""
        super().__init__("test.csv", *args, **kwargs)

    def _ground_truth_to_df(self, ground_truth: list[SingleImage], seed: int) -> pd.DataFrame:
        """Convert the ground truth list of images to a DataFrame."""
        random.seed(seed)
        random.shuffle(ground_truth)

        lines = []
        for img in ground_truth:
            for box, label_uid in zip(img.boxes, img.label_uids):
                lines.append(
                    {
                        "path": img.path,
                        "file_name": img.name,
                        "center_x": box[0],
                        "center_y": box[1],
                        "width": box[2],
                        "height": box[3],
                        "label": self.class_store.get_name(label_uid),
                    }
                )
        return pd.DataFrame(lines)

    def test_invalid_path(self) -> None:
        """Test exporting annotations to a CSV file with an invalid path."""
        with self.assertRaises(ValueError):
            export("invalid_path", "csv", self.image_store, self.class_store, True, 0.0)

    def test_all(self) -> None:
        """Test exporting annotations to a CSV file with a split and with all images.

        Here we expect the annotations to be split into training and validation data. We do not exclude images
        that are not marked as ready in this test case.
        """
        for split in [0.0, 0.25, 0.5, 0.75, 1.0]:
            self.tearDown()
            self.setUp()
            save_path = os.path.join(self.temp_dir.name, "test.csv")
            self.assertFalse(os.path.exists(self.temp_file))

            # add an additional image to the image store so we have 4 images in total
            self.image_store.add_images(self.additional_images[0])
            self.ground_truth_img_list.append(self.additional_images[0])

            self.init_all_images(self.ground_truth_img_list)
            self.init_all_images(self.image_store._images)

            export(save_path, "csv", self.image_store, self.class_store, False, split, 42)
            self.assertTrue(os.path.exists(self.temp_file))
            df_created = pd.read_csv(save_path, delimiter=";", header=0)
            df_true = self._ground_truth_to_df(self.ground_truth_img_list.copy(), 42)
            df_true["split"] = ["train"] * int(16 * (1 - split)) + ["test"] * int(16 * split)
            pd.testing.assert_frame_equal(df_created, df_true)

    def test_ready(self) -> None:
        """Test exporting annotations to a CSV file with a split and with ready images only.

        Here we expect the annotations to be split into training and validation data. We exclude images that
        are not marked as ready.
        """
        for split in [0.0, 0.25, 0.5, 0.75, 1.0]:
            self.tearDown()
            self.setUp()
            save_path = os.path.join(self.temp_dir.name, "test.csv")
            self.assertFalse(os.path.exists(self.temp_file))

            # add an additional image to the image store so we have 4 images in total
            self.image_store.add_images(self.cast(self.additional_images))
            self.ground_truth_img_list.append(self.additional_images[0])

            self.init_all_images(self.ground_truth_img_list)
            self.init_all_images(self.image_store._images)
            self.ready_all_images(self.ground_truth_img_list)
            self.ready_all_images(self.image_store._images)
            self.image_store._images[4].ready = False

            export(save_path, "csv", self.image_store, self.class_store, True, split, 42)
            self.assertTrue(os.path.exists(self.temp_file))
            df_created = pd.read_csv(save_path, delimiter=";", header=0)
            expected = [img for img in self.ground_truth_img_list if img.ready]
            df_true = self._ground_truth_to_df(expected, 42)
            df_true["split"] = ["train"] * int(16 * (1 - split)) + ["test"] * int(16 * split)
            pd.testing.assert_frame_equal(df_created, df_true)


class TestExportJSON(TestExportBase):
    """Class for testing the JSON export functionality."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the test case."""
        super().__init__("test.json", *args, **kwargs)

    def test_invalid_path(self) -> None:
        """Test exporting annotations to a JSON file with an invalid path."""
        with self.assertRaises(ValueError):
            export("invalid_path", "json", self.image_store, self.class_store, True, 0.0)

    def test_all(self) -> None:
        """Test exporting annotations to a JSON file with all images.

        Here we expect all images to be exported. We do not exclude images that are not marked as ready in
        this. Also, images without annotations are exported.
        """
        classes_json = self.class_store.classes

        for split in [0.0, 0.25, 0.5, 0.75, 1.0]:
            self.tearDown()
            self.setUp()
            save_path = os.path.join(self.temp_dir.name, "test.json")
            self.assertFalse(os.path.exists(self.temp_file))

            # add an additional image to the image store so we have 4 images in total
            self.image_store.add_images(self.additional_images[0])
            self.ground_truth_img_list.append(self.additional_images[0])

            for i in range(len(self.ground_truth_img_list)):
                if random.randint(1, 10) < 5:
                    self.image_store._images[i].init(self.mock_model)
                    self.ground_truth_img_list[i].init(self.mock_model)

            export(save_path, "json", self.image_store, self.class_store, False, split, seed=0)
            self.assertTrue(os.path.exists(self.temp_file))
            random.seed(0)
            random.shuffle(self.ground_truth_img_list)
            ground_truth = dict(
                class_mapping=classes_json,
                train=[img.to_dict() for img in self.ground_truth_img_list[: int(4 * (1 - split))]],
                test=[img.to_dict() for img in self.ground_truth_img_list[int(4 * (1 - split)) :]],
            )
            with open(save_path) as f:
                created = json.load(f)
            self.assertEqual(created, ground_truth)

    def test_ready(self) -> None:
        """Test exporting annotations to a JSON file with ready images only.

        Here we expect only ready images to be exported. Images without annotations are still exported.
        """
        classes_json = self.class_store.classes

        for split in [0.0, 0.25, 0.5, 0.75, 1.0]:
            self.tearDown()
            self.setUp()
            save_path = os.path.join(self.temp_dir.name, "test.json")
            self.assertFalse(os.path.exists(self.temp_file))

            # add an additional image to the image store so we have 4 images in total
            self.image_store.add_images(self.cast(self.additional_images))
            self.ground_truth_img_list.append(self.additional_images[0])

            for i in range(len(self.ground_truth_img_list)):
                if random.randint(1, 10) < 5:
                    self.image_store._images[i].init(self.mock_model)
                    self.ground_truth_img_list[i].init(self.mock_model)

            self.ready_all_images(self.ground_truth_img_list)
            self.ready_all_images(self.image_store._images)
            self.image_store._images[4].ready = False

            export(save_path, "json", self.image_store, self.class_store, True, split, seed=0)
            self.assertTrue(os.path.exists(self.temp_file))
            random.seed(0)
            random.shuffle(self.ground_truth_img_list)
            ground_truth = dict(
                class_mapping=classes_json,
                train=[img.to_dict() for img in self.ground_truth_img_list[: int(4 * (1 - split))]],
                test=[img.to_dict() for img in self.ground_truth_img_list[int(4 * (1 - split)) :]],
            )
            with open(save_path) as f:
                created = json.load(f)
            self.assertEqual(created, ground_truth)


class TestExportYOLO(TestExportBase):
    """Class for testing the YOLO export functionality."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the test case."""
        super().__init__("test", *args, **kwargs)

    def _check_folder_structure_and_yaml(self) -> None:
        """Check if the folder structure is correct."""
        self.assertTrue(os.path.exists(os.path.join(self.temp_file, "train", "images")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_file, "train", "labels")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_file, "test", "images")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_file, "test", "labels")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_file, "data.yaml")))

        with open(os.path.join(self.temp_file, "data.yaml")) as f:
            created = yaml.safe_load(f)
        self.assertEqual(created["train"], "../train/images")
        self.assertEqual(created["test"], "../test/images")
        self.assertEqual(created["nc"], len(self.class_store.get_class_names()))
        self.assertEqual(
            created["names"], {i: label for i, label in enumerate(self.class_store.get_class_names())}
        )

    def _check_img(self, ground_truth: list[SingleImage], seed: int, split: float) -> None:
        """Check if the images are correctly exported."""
        random.seed(seed)
        random.shuffle(ground_truth)
        train = ground_truth[: int(len(ground_truth) * (1 - split))]
        test = ground_truth[int(len(ground_truth) * (1 - split)) :]

        # make path to save images temporary
        tmp_path = os.path.join(self.temp_file, "tmp")
        os.makedirs(tmp_path, exist_ok=True)

        for split_name, data in zip(["train", "test"], [train, test]):
            for i, single_img in enumerate(data):
                img_path = os.path.join(self.temp_file, split_name, "images", f"{i}.jpg")
                self.assertTrue(os.path.exists(img_path))
                with Image.open(img_path) as img:
                    self.assertEqual(img.size, (640, 640))
                    with Image.open(single_img.path) as original:
                        original = original.resize((640, 640))

                        # we need to save the image and load it again to compare the images because during the
                        # compression to jpg the image is changed and when comparing the images the test fails
                        original.save(os.path.join(tmp_path, f"{i}_original.jpg"))
                        with Image.open(os.path.join(tmp_path, f"{i}_original.jpg")) as original_new:
                            self.assertTrue(((np.abs(np.array(img) - np.array(original_new))) < 3).all())

    def _load_yolo_as_df(self) -> pd.DataFrame:
        """Load the YOLO annotations as a DataFrame."""
        lines = []
        path = self.temp_file
        for split in ["train", "test"]:
            for label_file in os.listdir(os.path.join(path, split, "labels")):
                with open(os.path.join(path, split, "labels", label_file)) as f:
                    for line in f:
                        lines.append(
                            {
                                "path": os.path.join(split, "images", label_file.replace("txt", "jpg")),
                                "file_name": label_file.replace("txt", "jpg"),
                                "center_x": float(line.split(" ")[1]),
                                "center_y": float(line.split(" ")[2]),
                                "width": float(line.split(" ")[3]),
                                "height": float(line.split(" ")[4]),
                                "label": int(line.split(" ")[0]),
                            }
                        )
        return pd.DataFrame(lines)

    def _ground_truth_to_df(self, ground_truth: list[SingleImage], seed: int, split: float) -> pd.DataFrame:
        """Convert the ground truth list of images to a DataFrame."""
        random.seed(seed)
        random.shuffle(ground_truth)
        train = ground_truth[: int(len(ground_truth) * (1 - split))]
        test = ground_truth[int(len(ground_truth) * (1 - split)) :]

        def process(img_list: list[SingleImage], split: str) -> list[dict]:
            tmp = []
            for i, img in enumerate(img_list):
                for box, label_uid in zip(img.boxes, img.label_uids):
                    tmp.append(
                        {
                            "path": os.path.join(split, "images", f"{i}.jpg"),
                            "file_name": f"{i}.jpg",
                            "center_x": box[0],
                            "center_y": box[1],
                            "width": box[2],
                            "height": box[3],
                            "label": label_uid,
                        }
                    )
            return tmp

        lines = process(train, "train")
        lines.extend(process(test, "test"))
        df = pd.DataFrame(lines)
        return df

    def test_all(self) -> None:
        """Test exporting annotations to a JSON YOLO format.

        Here we expect all images to be exported. We do not exclude images that are not marked as ready in
        this. Also, images without annotations are exported.
        """
        for split in [0.0, 0.25, 0.5, 0.75, 1.0]:
            self.tearDown()
            self.setUp()
            self.assertFalse(os.path.exists(self.temp_file))

            # add an additional image to the image store so we have 4 images in total
            self.image_store.add_images(self.additional_images[0])
            self.ground_truth_img_list.append(self.additional_images[0])

            for i in range(len(self.ground_truth_img_list)):
                if random.randint(1, 10) < 5:
                    self.image_store._images[i].init(self.mock_model)
                    self.ground_truth_img_list[i].init(self.mock_model)

            export(self.temp_file, "yolo", self.image_store, self.class_store, False, split, seed=0)
            self._check_folder_structure_and_yaml()
            df_created = self._load_yolo_as_df()
            df_true = self._ground_truth_to_df(self.ground_truth_img_list.copy(), seed=0, split=split)
            pd.testing.assert_frame_equal(df_created, df_true)
            self._check_img(self.ground_truth_img_list.copy(), seed=0, split=split)

    def test_ready(self) -> None:
        """Test exporting annotations to a JSON YOLO format with ready images only.

        Here we expect only ready images to be exported. Images without annotations are still exported.
        """
        for split in [0.0, 0.25, 0.5, 0.75, 1.0]:
            self.tearDown()
            self.setUp()
            self.assertFalse(os.path.exists(self.temp_file))

            # add an additional image to the image store so we have 4 images in total
            self.image_store.add_images(self.cast(self.additional_images))
            self.ground_truth_img_list.append(self.additional_images[0])

            for i in range(len(self.ground_truth_img_list)):
                if random.randint(1, 10) < 5:
                    self.image_store._images[i].init(self.mock_model)
                    self.ground_truth_img_list[i].init(self.mock_model)

            self.ready_all_images(self.ground_truth_img_list)
            self.ready_all_images(self.image_store._images)
            self.image_store._images[4].ready = False

            export(self.temp_file, "yolo", self.image_store, self.class_store, True, split, seed=0)
            self._check_folder_structure_and_yaml()
            df_created = self._load_yolo_as_df()
            df_true = self._ground_truth_to_df(self.ground_truth_img_list.copy(), seed=0, split=split)
            pd.testing.assert_frame_equal(df_created, df_true)
            self._check_img(self.ground_truth_img_list.copy(), seed=0, split=split)

    def test_dir_not_existing_yet(self) -> None:
        """Test exporting annotations to a YOLO format, where the directory does not exist yet."""
        # remove the last "/test" from self.file_name
        self.temp_file = self.temp_file[: -len("test")]
        export(self.temp_file, "yolo", self.image_store, self.class_store, True, 0.0)
        self._check_folder_structure_and_yaml()
