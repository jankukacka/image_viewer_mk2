# ------------------------------------------------------------------------------
#  File: window_about.py
#  Author: Jan Kukacka
#  Date: 11/2021
# ------------------------------------------------------------------------------
#  Implementation of the About window
# ------------------------------------------------------------------------------

import tkinter as tk
import tkinter.ttk as ttk
import os
from pathlib import Path
from PIL import Image, ImageOps, ImageTk
import numpy as np

try:
    from importlib import metadata
except ImportError: # for Python<3.8
    import importlib_metadata as metadata
__version__ = metadata.version('image-viewer-mk2')


def prepare_icon(filename, skin):
    path = Path(os.path.dirname(os.path.abspath(__file__)))
    icon = Image.open(str(path.parent/'resources'/filename))
    icon2 = icon.convert('RGB')
    icon2 = ImageOps.invert(icon2)
    icon2 = Image.fromarray(np.concatenate([np.array(icon2), np.array(icon)[...,-1,None]], axis=-1), mode='RGBA')
    bkg = Image.new(mode='RGBA', size=icon.size, color=skin.bg_color)
    icon = Image.alpha_composite(bkg, icon2).convert('RGB')
    icon = ImageTk.PhotoImage(icon)
    return icon


class WindowAbout(tk.Toplevel):

    def __init__(self, master, skin):
        tk.Toplevel.__init__(self, master)
        self.master = master
        self.skin = skin

        self.title('About')
        self.mainframe = tk.Frame(self, background=self.skin.bg_color)
        self.mainframe.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        ## Hide window on closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        frame = tk.Frame(self.mainframe, bg=self.skin.bg_color)
        frame.grid(column=0, row=0, sticky='nwes')

        icon = prepare_icon('logo128.png', self.skin)
        tk.Label(frame, image=icon, bg=self.skin.bg_color).pack(side=tk.TOP, pady=100, padx=30)
        self.icon = icon

        frame = tk.Frame(self.mainframe, bg=self.skin.bg_color)
        frame.grid(column=1, row=0, sticky='nwes')

        frame = tk.Frame(frame, bg='#ff0000')
        frame.pack(side=tk.TOP, expand=True, fill=tk.X, padx=10)
        tk.Label(frame, text='Image Viewer MK2', fg=self.skin.fg_color, bg=self.skin.bg_color, font=('Segoe UI', 14, 'bold')).pack(side=tk.TOP, expand=False, fill=tk.X)
        tk.Label(frame, text=f'v{__version__} (2022-03-14)', fg=self.skin.fg_color, bg=self.skin.bg_color).pack(side=tk.TOP, expand=False, fill=tk.X)
        tk.Label(frame, text='Author: Jan Kukačka, 2021', fg=self.skin.fg_color, bg=self.skin.bg_color).pack(side=tk.TOP, expand=False, fill=tk.X)
        tk.Label(frame, text='Provided under MIT license.', fg=self.skin.fg_color, bg=self.skin.bg_color).pack(side=tk.TOP, expand=False, fill=tk.X)
        tk.Label(frame, text='Icon credits: Icon home, Gregor Cresnar,\nFreepik, Google, Uptal Barman\nArkinasi, Royyan Wijaya and Pancracysdh.', fg=self.skin.fg_color, bg=self.skin.bg_color).pack(side=tk.TOP, expand=False, fill=tk.X)

    def on_closing(self):
        self.master.window_about = None
        self.withdraw()
