from abc import ABC, abstractmethod

import customtkinter as ctk


class UI(ABC, ctk.CTkFrame):

    def __init__(self, master: ctk.CTk):
        super().__init__(master)

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

    @abstractmethod
    def refresh_headerbar(self):
        pass
