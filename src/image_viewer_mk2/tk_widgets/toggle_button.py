# ------------------------------------------------------------------------------
#  File: toggle_button.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Toggle button widget
# ------------------------------------------------------------------------------

import tkinter as tk
import tkinter.ttk as ttk

class ToggleButton(ttk.Button):
    def __init__(self, parent, image_on, image_off, variable=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.image_on = tk.PhotoImage(file=str(image_on))
        self.image_off = tk.PhotoImage(file=str(image_off))

        self._variable = None
        self._variable_trace_id = None

        if variable is not None:
            self.variable = variable
        else:
            self.variable = tk.BooleanVar(value=False)


        self.bind('<Button-1>', self.on_click)

    @property
    def variable(self):
        return self._variable

    @variable.setter
    def variable(self, val):
        if val is not self._variable:
            if self._variable_trace_id is not None:
                self._variable.trace_vdelete('w', self._variable_trace_id)
            self._variable = val
            self._variable_trace_id = self._variable.trace('w', self.on_modechanged)
            self.on_modechanged()

    def on_click(self, event):
        self.variable.set(not self.variable.get())

    def on_modechanged(self, *args):
        ## Update image
        if self.variable.get():
            self.configure(image=self.image_on)
        else:
            self.configure(image=self.image_off)
