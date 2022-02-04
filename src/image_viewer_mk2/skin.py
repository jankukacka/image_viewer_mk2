# ------------------------------------------------------------------------------
#  File: skin.py
#  Author: Jan Kukacka
#  Date: 4/2020
# ------------------------------------------------------------------------------
#  Appearance definitions
# ------------------------------------------------------------------------------
import tkinter.font as tkFont
import tkinter.ttk as ttk

class Skin(object):
    '''
    Skin class with definitions of appearance properties
    '''

    def __init__(self):
        '''
        Initialize properties of a default skin
        '''

        self.bg_color = '#444444'
        # self.bg_color = '#ffffff'
        self.bg_highlight_color = '#666666'
        self.fg_color = '#FFFFFF'
        # self.fg_color = '#000000'
        self.fg_warning_color = '#E63F06'

        self.font_heading = tkFont.Font(family='ansi', size=9, weight=tkFont.BOLD)

        ttk.Style().configure("TLabelframe", background=self.bg_color)
        ttk.Style().configure("TLabelframe.Label", font=self.font_heading, background=self.bg_color, foreground=self.fg_color)
        ttk.Style().configure("TRadiobutton", background=self.bg_color, foreground=self.fg_color)
        ttk.Style().configure("TScale", background=self.bg_color, foreground=self.fg_color)
        ttk.Style().configure("TCheckbutton", background=self.bg_color, foreground=self.fg_color)
        ttk.Style().configure("Highlight.TCheckbutton", background=self.bg_highlight_color)
