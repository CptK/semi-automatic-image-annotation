from abc import ABC, abstractmethod

import customtkinter as ctk


class UI(ABC, ctk.CTk):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def refresh_all(self):
        pass

    @abstractmethod
    def redraw_content(self):
        pass

    @abstractmethod
    def refresh_left_sidebar(self):
        pass

    @abstractmethod
    def refresh_right_sidebar(self):
        pass
