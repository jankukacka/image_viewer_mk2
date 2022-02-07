# ------------------------------------------------------------------------------
#  File: loader_animation.py
#  Author: Jan Kukacka
#  Date: 3/2021
# ------------------------------------------------------------------------------
#  Class that implements loader animation in the view
# ------------------------------------------------------------------------------

import os
from PIL import Image, ImageTk, ImageSequence, ImageChops, ImageEnhance
from pathlib import Path

class LoaderAnimation(object):

    def __init__(self, position, bg_color, tk_canvas, tk):
        '''
        # Arguments:
        - `bg_color`: background color of the loader animation.
        '''
        self.position = position
        self.bg_color = bg_color
        self.tk_canvas = tk_canvas
        self.tk = tk

        path = Path(os.path.dirname(os.path.abspath(__file__))).parent / 'resources' / 'loader.gif'
        img = Image.open(path)

        self.prepare_frames(img)

        self._is_playing = False
        self._active_frame = 0
        self._dim_level = 0

    def prepare_frames(self, img):
        self.frames = [im.copy().crop((130,120,270,183)) for im in ImageSequence.Iterator(img)]
        for i in range(len(self.frames)):
            bkg = Image.new("RGB", self.frames[i].size, self.bg_color)
            frame = ImageChops.add(bkg, ImageChops.invert(self.frames[i].convert('RGB')))
            frame = frame.convert("HSV")

            # adjust = Image.new("HSV", frame.size, (140,0,0))
            # frame = ImageChops.add_modulo(frame, adjust)
            # adjust = Image.new("HSV", frame.size, (0,0,0))
            # frame = ImageChops.add(frame, adjust)
            frame = frame.convert("RGBA")

            gray = ImageChops.invert(self.frames[i].convert('L'))
            E1 = ImageEnhance.Contrast(gray)

            frame.putalpha(E1.enhance(2))#ImageChops.multiply(gray, gray))
            # bkg = Image.new("RGB", frame.size, self.bg_color)
            # self.frames[i] = ImageChops.screen(bkg, ImageChops.invert(frame))
            self.frames[i] = frame

    def show(self):
        if not self._is_playing:
            self._is_playing = True
        if self._dim_level <= 0:
            self.tk.after(10, self._update)

    def hide(self):
        self._is_playing = False

    def _update(self):
        frame = self.frames[self._active_frame]
        if self._dim_level < 1:
            frame = frame.copy()
            dim = frame.getchannel('A')
            E = ImageEnhance.Brightness(dim)
            frame.putalpha(E.enhance(self._dim_level))

        self._render_ref = ImageTk.PhotoImage(frame)
        self.tk_canvas.create_image((self.tk_canvas.winfo_width()/2, self.tk_canvas.winfo_height()/2), image=self._render_ref)
        self._active_frame = (self._active_frame + 1) % len(self.frames)

        if self._is_playing or self._dim_level > 0:
            self.tk.after(20, self._update)

        if self._is_playing and self._dim_level < 1:
            self._dim_level += 0.05
        if not self._is_playing and self._dim_level > 0:
            self._dim_level -= 0.01
