"""Left sidebar for the annotator GUI."""

from collections.abc import Callable

import customtkinter as ctk

from annotator.controller import Controller


class ListButton(ctk.CTkButton):
    """Button for the left sidebar list items.

    Args:
        master: The parent widget.
        text: The text to display on the button.
        command: The command to call when the button is clicked.
        active: Whether the button is currently active.
    """

    def __init__(self, master, text, command, active: bool = False, **kwargs) -> None:
        text_color = "black" if active else "gray"
        super().__init__(
            master,
            text=text,
            command=command,
            fg_color="transparent",
            text_color=text_color,
            height=8,
            **kwargs,
        )

    def update(self, active: bool) -> None:
        """Update the button appearance based on the active status.

        Args:
            active: Whether the button is currently active.
        """
        text_color = "black" if active else "gray"
        self.configure(text_color=text_color)


class ListItem(ctk.CTkFrame):
    """List item for the left sidebar.

    Args:
        master: The parent widget.
        text: The text to display on the list item.
        command: The command to call when the item is clicked.
        active: Whether the item is currently active.
        ready: Whether the item is marked as ready.
    """

    def __init__(self, master, text: str, command: Callable, active: bool, ready: bool, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.button = ListButton(self, text=text, command=command, active=active)
        label_text = "✓" if ready else " "
        self.label = ctk.CTkLabel(
            self, text=label_text, fg_color="transparent", text_color="green", font=("Arial", 12)
        )
        self.label.pack(side="right", padx=5)
        self.button.pack(fill="x", padx=5, pady=5)

    def update(self, active, ready) -> None:
        """Update the list item appearance based on the active status and readiness.

        Args:
            active: Whether the item is currently active.
            ready: Whether the item is marked as ready.
        """
        text = "✓" if ready else " "
        self.label.configure(text=text)
        self.button.update(active)


class LeftSidebar(ctk.CTkScrollableFrame):
    """Left sidebar for the annotator application.

    Args:
        master: The parent widget.
        controller: The controller object.
    """

    def __init__(self, master, controller: Controller, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.controller = controller
        self.setup()

    def setup(self) -> None:
        """Set up the left sidebar list items."""
        self.list_items: list[ListItem] = []
        for i, name in enumerate(self.controller.image_names()):
            button = ListItem(
                self,
                text=name,
                command=lambda i=i: self.controller.jump_to(i),
                active=i == self.controller.current_index(),
                ready=self.controller[i].ready,
            )
            button.pack(fill="x", padx=5, pady=5)
            self.list_items.append(button)

    def update(self) -> None:
        """Update the left sidebar list items."""
        for i, list_item in enumerate(self.list_items):
            list_item.update(
                active=i == self.controller.current_index(),
                ready=self.controller[i].ready,
            )
