# ------------------------------------------------------------------------------
#  File: slider.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Widget containing configuration with a slider
# ------------------------------------------------------------------------------


import tkinter as tk
import tkinter.ttk as ttk

try:
    from .limiter import Limiter
except ImportError:
    from tk_widgets.limiter import Limiter

class Slider(tk.Frame):
    def __init__(self, parent, title, variable, limit_low, limit_high, resolution, skin, *args, **kwargs):
        super().__init__(parent, bg=skin.bg_color, *args, **kwargs)

        self.skin = skin

        ## Top label
        if title is not None:
            label = tk.Label(self, text=title, fg=self.skin.fg_color,
                             bg=self.skin.bg_color, anchor=tk.NW)
            label.pack(side=tk.TOP, expand=False, fill=tk.X)

        ## Pad-x compensates for entry starting too left
        grid = tk.Frame(self, bg=self.skin.bg_color)
        grid.pack(side=tk.TOP, expand=True, fill=tk.X, padx=(3,0))

        label = ttk.Entry(grid, textvariable=variable, width=6)
        label.pack(side=tk.LEFT, expand=False, fill=tk.BOTH)
        ## Left label
        label = tk.Label(grid, text='{}'.format(limit_low),
                         fg=self.skin.fg_color, bg=self.skin.bg_color, anchor=tk.NE, width=4)
        label.pack(side=tk.LEFT, expand=False, fill=tk.BOTH)
        scale = Limiter(grid, from_=limit_low, to=limit_high, resolution=resolution,
                        orient=tk.HORIZONTAL, variable=variable)
        scale.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ## Right label
        label = tk.Label(grid, text='{}'.format(limit_high),
                         fg=self.skin.fg_color, bg=self.skin.bg_color, anchor=tk.NE, width=4)
        label.pack(side=tk.LEFT, expand=False, fill=tk.BOTH)
