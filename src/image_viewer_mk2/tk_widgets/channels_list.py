# ------------------------------------------------------------------------------
#  File: channels_list.py
#  Author: Jan Kukacka
#  Date: 11/2021
# ------------------------------------------------------------------------------
#  Viewer component for displaying the list of channels
# ------------------------------------------------------------------------------

import tkinter as tk
import tkinter.ttk as ttk

import os
import numpy as np
from pathlib import Path
from PIL import Image, ImageOps, ImageTk

try:
    from .scrolled_frame import ScrolledFrame
    from ..utils import event_handler
    from ..utils.tk_lazy_var import StringVar, BooleanVar
except ImportError:
    from tk_widgets.scrolled_frame import ScrolledFrame
    from utils import event_handler
    from utils.tk_lazy_var import StringVar, BooleanVar


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

class ChannelsList():

    def __init__(self, parent_frame, skin, var_selected_channel):
        self.skin = skin

        self.var_selected_channel = var_selected_channel
        self.var_channels = []
        self.mainframe = ttk.LabelFrame(parent_frame, text='Channels', padding=5)
        self.mainframe.pack(side=tk.TOP, expand=False, fill=tk.BOTH, padx=5, pady=5)

        header_frame = tk.Frame(self.mainframe, bg=self.skin.bg_color)
        header_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=0, pady=0)

        icon_eye = prepare_icon('eye16.png', self.skin)
        label = tk.Label(header_frame, image=icon_eye, bg=self.skin.bg_color)
        label.image = icon_eye
        label.pack(side=tk.LEFT, padx=3)

        icon_color = prepare_icon('color16.png', self.skin)
        label = tk.Label(header_frame, image=icon_color, bg=self.skin.bg_color)
        label.image = icon_color
        label.pack(side=tk.LEFT, padx=0)

        tk.Label(header_frame, text='Channel name', bg=self.skin.bg_color, fg=self.skin.fg_color).pack(side=tk.LEFT, padx=3)

        self.wrap_frame = ScrolledFrame(self.mainframe, bg=self.skin.bg_color,
                                        use_ttk=True, scrollbars='vertical',
                                        borderwidth=0, relief=tk.FLAT,
                                        width=200, height=600)
        self.wrap_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=0, pady=0)
        self.wrap_frame.bind_scroll_wheel(self.mainframe)
        self.wrap_frame.bind_scroll_wheel(self.wrap_frame)

        self.item_frame = None

        footer_frame = tk.Frame(self.mainframe, bg=self.skin.bg_color)
        footer_frame.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH, padx=0, pady=0)
        self.btn_hide_all = ttk.Button(footer_frame, text='Hide all')
        self.btn_hide_all.pack(side=tk.LEFT, expand=False, padx=5, pady=5)
        self.btn_show_all = ttk.Button(footer_frame, text='Show all')
        self.btn_show_all.pack(side=tk.LEFT, expand=False, pady=5)


    def recreate_items(self, channel_props):
        if self.item_frame is not None:
            self.item_frame.destroy()
            self.item_frame = None

        self.items_frame = self.wrap_frame.display_widget(tk.Frame, fit_width=True)

        while len(self.var_channels) > 0:
            for var in self.var_channels[0].values():
                for trace_info in var.trace_vinfo():
                    var.trace_vdelete(*trace_info)
            self.var_channels.pop(0)

        for channel_prop in channel_props:
            self.var_channels.append({'color': StringVar(value=channel_prop['color']),
                                      'visible': BooleanVar(value=channel_prop['visible']),
                                      'name': StringVar(value='Channel name')})

        self.color_previews = []
        self.item_frames = []
        def add_channel_entry(channel_index, var_channel):
            bind_tag = f'ChannelSelect{channel_index}'
            frame = tk.Frame(self.items_frame, bg=self.skin.bg_color)
            frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=0, pady=0)
            frame.bindtags((bind_tag,) + frame.bindtags())
            self.wrap_frame.bind_scroll_wheel(frame)
            self.item_frames.append(frame)

            frame.checkbox = ttk.Checkbutton(frame, text='', variable=var_channel['visible'],
                                             onvalue=True, offvalue=False)
            frame.checkbox.pack(side=tk.LEFT, expand=False, pady=2, padx=3)
            self.wrap_frame.bind_scroll_wheel(frame.checkbox)
            frame.checkbox.bindtags((bind_tag,) + frame.checkbox.bindtags())

            color_preview = tk.Frame(frame, width=16, height=16, bg=var_channel['color'].get(), highlightthickness=1, highlightbackground='#000000')
            color_preview.pack(side=tk.LEFT)
            color_preview.bindtags((bind_tag,) + color_preview.bindtags())

            self.wrap_frame.bind_scroll_wheel(color_preview)
            self.color_previews.append(color_preview)

            def on_colorchange(obj, var):
                obj.config(background=str(var.get()))
            handler = event_handler.TkVarEventHandler(on_colorchange, obj=color_preview, var=var_channel['color'])
            var_channel['color'].trace('w', handler)

            label = tk.Label(frame, textvariable=var_channel['name'], fg=self.skin.fg_color,
                             bg=self.skin.bg_color, anchor=tk.NW)
            label.pack(side=tk.LEFT, pady=2, padx=3)
            label.bindtags((bind_tag,) + label.bindtags())
            frame.label = label
            self.wrap_frame.bind_scroll_wheel(label)

            handler = event_handler.TkEventHandler(self.channel_onselect, var_channel_name=var_channel['name'])
            frame.bind_class(bind_tag, '<Button-1>', handler)
            handler = event_handler.TkEventHandler(self.init_rename_channel, channel_index=channel_index)
            frame.bind_class(bind_tag, '<Double-Button-1>', handler)

        for channel_index, var_channel in enumerate(self.var_channels):
            add_channel_entry(channel_index, var_channel)

    def update_vars(self, channel_props):
        for channel_property, var_channel in zip(channel_props, self.var_channels):
            for key in var_channel:
                var_channel[key].set(channel_property[key])


    def init_rename_channel(self, channel_index):
        frame = self.item_frames[channel_index]
        frame.label.pack_forget()
        entry = ttk.Entry(frame, width=25)
        entry.insert(0, self.var_channels[channel_index]['name'].get())
        entry.pack(side=tk.LEFT)
        entry.focus_set()
        entry.select_range(0, tk.END)
        handler = event_handler.TkEventHandler(self.end_rename_channel, frame=frame, entry=entry, channel_index=channel_index)
        entry.bind('<FocusOut>', handler)
        entry.bind('<Return>', handler)
        handler = event_handler.TkEventHandler(self.cancel_rename_channel, frame=frame, entry=entry)
        entry.bind('<Escape>', handler)

    def end_rename_channel(self, frame, entry, channel_index):
        value = entry.get()
        ## Check the value does not exist yet
        if value not in [vc['name'].get() for vc in self.var_channels]:
            old_value = self.var_channels[channel_index]['name'].get()
            self.var_channels[channel_index]['name'].set(value)
            ## Update also var_selected_channel if needed
            if self.var_selected_channel.get() == old_value:
                self.var_selected_channel.set(value)
        entry.destroy()
        frame.label.pack(side=tk.LEFT, pady=2, padx=3)

    def cancel_rename_channel(self, frame, entry):
        entry.destroy()
        frame.label.pack(side=tk.LEFT, pady=2, padx=3)

    @event_handler.requires('event')
    def channel_onselect(self, event, var_channel_name):
        event.widget.focus_set()
        self.var_selected_channel.set(var_channel_name.get())

    def highlight_item(self, item_index):
        for frame in self.item_frames:
            frame.config(bg=self.skin.bg_color)
            frame.checkbox.configure(style='TCheckbutton')
            frame.label.config(bg=self.skin.bg_color)
        self.item_frames[item_index].config(bg=self.skin.bg_highlight_color)
        self.item_frames[item_index].checkbox.configure(style='Highlight.TCheckbutton')
        self.item_frames[item_index].label.config(bg=self.skin.bg_highlight_color)
