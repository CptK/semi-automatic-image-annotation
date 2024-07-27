"""A module for storing and managing object classes."""

from typing import Any


class ClassesStore:
    """A class for storing and managing object classes.

    Each class is represented as a dictionary with the keys
    - 'uid': The unique identifier of the class.
    - 'name': The name of the class.
    - 'color': The color of the class.
    - 'default': Whether the class is the default class.

    Args:
        classes: A list of class dictionaries or class names.
    """

    DEFAULT_COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF"]

    def __init__(self, classes: list[dict[str, str]] | list[str]):
        self.classes: list[dict[str, Any]] = []

        if isinstance(classes[0], str):
            for i, name in enumerate(classes):
                self.add_class(
                    i, str(name), self.DEFAULT_COLORS[len(self.classes) % len(self.DEFAULT_COLORS)], i == 0
                )
        else:
            self.classes = classes  # type: ignore
            if not any(cls["default"] for cls in self.classes):
                self.classes[0]["default"] = True
            # if there is more than one default, only the first one is kept
            if sum(cls["default"] for cls in self.classes) > 1:
                first_default_idx = next(
                    i for i, cls in enumerate(self.classes) if cls["default"]
                )  # pragma: no cover
                for i, cls in enumerate(self.classes):
                    if i != first_default_idx:
                        cls["default"] = False

    def add_class(self, uid: int, name: str, color: str, is_default: bool = False) -> dict[str, Any]:
        """Add a class to the store.

        Args:
            uid: The unique identifier of the class.
            name: The name of the class.
            color: The color of the class.
            is_default: Whether the class is the default class.

        Returns:
            The dictionary representing the new class.

        Raises:
            ValueError: If a class with the same UID or name already exists, or if more than one class is set
                        as default.
        """
        if any(cls["uid"] == uid for cls in self.classes):
            raise ValueError("Class with the same UID already exists.")

        if any(cls["name"] == name for cls in self.classes):
            raise ValueError("Class with the same name already exists.")

        if is_default and any(cls["default"] for cls in self.classes):
            raise ValueError("Only one class can be the default class.")

        self.classes.append({"uid": uid, "name": name, "color": color, "default": is_default})
        return self.classes[-1]

    def delete_class(self, uid: int) -> None:
        """Delete a class from the store.

        If the class is the default class, the first class in the list is set as the new default.

        Args:
            uid: The unique identifier of the class.
        """
        self.classes = [cls for cls in self.classes if cls["uid"] != uid]
        if not any(cls["default"] for cls in self.classes):
            self.classes[0]["default"] = True

    def get_class_names(self) -> list[str]:
        """Returns a list of all class names."""
        return [cls["name"] for cls in self.classes]

    def get_class_uids(self) -> list[int]:
        """Returns a list of all class UIDs."""
        return [cls["uid"] for cls in self.classes]

    def get_next_color(self) -> str:
        """Returns the next color in the default color list."""
        return self.DEFAULT_COLORS[len(self.classes) % len(self.DEFAULT_COLORS)]

    def get_next_class_name(self) -> str:
        """Returns the next class name in the default naming scheme."""
        name = f"Class {len(self.classes) + 1}"
        while any(item == name for item in self.get_class_names()):
            name = f"Class {int(name.split()[-1]) + 1}"
        return name

    def get_next_uid(self) -> int:
        """Returns the next available unique identifier."""
        ids = [cls["uid"] for cls in self.classes]
        return int(max(ids)) + 1 if ids else 0

    def get_default_uid(self) -> int:
        """Returns the unique identifier of the default class."""
        return int(next(cls["uid"] for cls in self.classes if cls["default"]))  # pragma: no cover

    def set_default_uid(self, uid: int) -> None:
        """Set the default class by its unique identifier. The previous default class is unset."""
        default_class = next(cls for cls in self.classes if cls["default"])  # pragma: no cover
        default_class["default"] = False
        next(cls for cls in self.classes if cls["uid"] == uid)["default"] = True  # pragma: no cover

    def get_color(self, uid: int) -> str:
        """Returns the color of a class by its unique identifier."""
        return str(next(cls["color"] for cls in self.classes if cls["uid"] == uid))  # pragma: no cover

    def get_default_class(self) -> dict[str, Any]:
        """Returns the default class."""
        return next(cls for cls in self.classes if cls["default"])  # pragma: no cover

    def change_name(self, uid: int | list[int], name: str | list[str]) -> None:
        """Change the name of a class or a list of classes by their unique identifiers.

        Args:
            uid: The unique identifier of the class or a list of unique identifiers.
            name: The new name of the class or a list of new names.

        Raises:
            ValueError: If the number of UIDs and names do not match.
        """
        if isinstance(uid, int):
            uid = [uid]
            name = [name]  # type: ignore

        if len(uid) != len(name):
            raise ValueError("Number of UIDs and names do not match.")

        if any(n in self.get_class_names() for n in name):
            raise ValueError("Class with the same name already exists.")

        if len(set(name)) != len(name):
            raise ValueError("Class names must be unique.")

        for i, n in zip(uid, name):
            next(cls for cls in self.classes if cls["uid"] == i)["name"] = n  # pragma: no cover

    def change_color(self, uid: int, color: str) -> None:
        """Change the color of a class by its unique identifier."""
        next(cls for cls in self.classes if cls["uid"] == uid)["color"] = color  # pragma: no cover

    def get_name(self, uid: int) -> str:
        """Returns the name of a class by its unique identifier."""
        return str(next(cls["name"] for cls in self.classes if cls["uid"] == uid))  # pragma: no cover

    def get_uid(self, name: str) -> int:
        """Returns the unique identifier of a class by its name"""
        return int(next(cls["uid"] for cls in self.classes if cls["name"] == name))  # pragma: no cover

    def __getitem__(self, idx: int):
        return self.classes[idx]

    def __len__(self):
        return len(self.classes)

    def __iter__(self):
        return iter(self.classes)
