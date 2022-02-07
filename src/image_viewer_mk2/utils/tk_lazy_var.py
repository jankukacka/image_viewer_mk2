# ------------------------------------------------------------------------------
#  File: tk_lazy_var.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Lazy variables that only trigger 'write' trace events when their value
#  really changes
# ------------------------------------------------------------------------------

import tkinter as tk

class StringVar(tk.StringVar):
    def set(self, val):
        if val != self.get():
            super().set(val)

class BooleanVar(tk.BooleanVar):
    def set(self, val):
        if val != self.get():
            super().set(val)

class DoubleVar(tk.DoubleVar):
    def set(self, val):
        if val != self.get():
            super().set(val)

class IntVar(tk.IntVar):
    def set(self, val):
        if val != self.get():
            super().set(val)
