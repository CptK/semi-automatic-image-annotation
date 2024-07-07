from collections.abc import Callable
from tkinter import IntVar, StringVar, colorchooser

import customtkinter as ctk

from annotator.controller import Controller


class ClassItem(ctk.CTkFrame):
    def __init__(
        self,
        master,
        controller: Controller,
        class_name: str,
        class_color: str,
        default_class_uid: IntVar,
        uid: int,
        delete_callback: Callable,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.controller = controller

        self.class_name = StringVar(value=class_name)

        self.delete_callback = delete_callback
        self.uid = uid

        self.entry = ctk.CTkEntry(self, textvariable=self.class_name)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.radio = ctk.CTkRadioButton(self, text="", variable=default_class_uid, value=uid)
        self.radio.pack(side="left", padx=(10, 10))

        self.color_button = ctk.CTkButton(
            self, text="", width=20, fg_color=class_color, command=self.choose_color
        )
        self.color_button.pack(side="left", padx=(10, 10))

        self.delete_button = ctk.CTkButton(self, text="X", command=self.delete_item)
        self.delete_button.pack(side="left", padx=(10, 10))

    def choose_color(self):
        color_code = colorchooser.askcolor(title="Choose color")[1]
        if color_code:
            self.color_button.configure(fg_color=color_code)
            self.controller.change_class_color(self.uid, color_code)

    def delete_item(self):
        self.delete_callback(self)


class ClassesContainer(ctk.CTkScrollableFrame):
    def __init__(self, master, controller: Controller, can_delete: Callable, **kwargs):
        super().__init__(master, **kwargs)
        self.class_items: list[ClassItem] = []
        self.controller = controller
        self.can_delete = can_delete

        self.default_class_uid = IntVar(value=self.controller.get_default_class_uid())
        self.default_class_uid.trace_add("write", self.update_default_uid)

        for cls in self.controller.class_iter():
            self.add_class_item(cls["name"], cls["color"], cls["uid"])

    def add_class_item(self, class_name, class_color, uid: int):
        class_item = ClassItem(
            self,
            self.controller,
            class_name,
            class_color,
            self.default_class_uid,
            uid,
            self.delete_class_item,
        )
        class_item.pack(fill="x", pady=(0, 5))
        self.class_items.append(class_item)

    def delete_class_item(self, del_item: ClassItem):
        if not self.can_delete(del_item.uid):
            return
        del_item.pack_forget()
        self.class_items.remove(del_item)
        self.controller.delete_class(del_item.uid)

    def update_default_uid(self, *args):
        self.controller.set_default_class_uid(self.default_class_uid.get())


class ClassesPopup(ctk.CTkToplevel):

    def __init__(self, master, controller: Controller, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Classes")
        self.geometry("400x400")
        self.controller = controller

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        self.warning_label = ctk.CTkLabel(self.container, text="", text_color="red")
        self.warning_label.pack(pady=(0, 10))

        self.classes_container = ClassesContainer(self.container, self.controller, self.can_delete)
        self.classes_container.pack(fill="both", expand=True, pady=(0, 20))

        self.add_class_button = ctk.CTkButton(self.container, text="Add Class", command=self.add_class)
        self.add_class_button.pack(side="left", padx=(0, 10))

        self.done_button = ctk.CTkButton(self.container, text="Done", command=self.on_done)
        self.done_button.pack(side="right")

    def add_class(self):
        new_class = self.controller.add_new_init_class()
        self.classes_container.add_class_item(new_class["name"], new_class["color"], new_class["uid"])

    def can_delete(self, uid: int):
        if len(self.controller.get_number_classes()) == 1:
            self.warning_label.configure(text="Cannot delete the last class.")
            return False
        if self.controller.get_default_class_uid() == uid:
            self.warning_label.configure(text="Cannot delete the default class.")
            return False
        return True

    def on_done(self):
        class_names = [item.class_name.get() for item in self.classes_container.class_items]
        if len(class_names) != len(set(class_names)):
            self.warning_label.configure(text="Cannot have two classes with the same name.")
            return

        uids = [item.uid for item in self.classes_container.class_items]
        self.controller.change_class_name(uids, class_names)

        self.destroy()
