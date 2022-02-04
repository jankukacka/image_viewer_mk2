# ------------------------------------------------------------------------------
#  File: link_button.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Link button widget
# ------------------------------------------------------------------------------

import tkinter as tk
import tkinter.ttk as ttk

class LinkButton(tk.Label):
    def __init__(self, parent, skin, *args, command=None, **kwargs):
        super().__init__(parent, *args, bg=skin.bg_color, fg=skin.fg_color, **kwargs)
        self.skin = skin
        self.default_font = tk.font.nametofont(self.cget('font'))
        self.highlight_font = self.default_font.copy()
        self.highlight_font.config(underline=1)
        self.bind('<Enter>', self.on_mouseover)
        self.bind('<Leave>', self.on_mouseout)

        self._command = None
        self._command_binding = None
        self.command = command

    @property
    def command(self):
        return self._command

    @command.setter
    def command(self, val):
        if val is not self._command:
            self._command = val
            if self._command_binding is not None:
                self.unbind('<ButtonRelease-1>', self._command_binding)
            if self._command is not None:
                self._command_binding = self.bind('<ButtonRelease-1>', self._command)

    def on_mouseover(self, event):
        self.config(fg=self.skin.fg_warning_color, font=self.highlight_font)

    def on_mouseout(self, event):
        self.config(fg=self.skin.fg_color, font=self.default_font)
