# ------------------------------------------------------------------------------
#  File: sortable_accordion.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  TkInter implementation of a widget that supports sorting and folding of items
# ------------------------------------------------------------------------------

import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
import os

try:
    from ..ObservableCollections.observablelist import ObservableList
    from ..ObservableCollections.observabledict import ObservableDict
    from ..ObservableCollections.observable import Observable
    from ..ObservableCollections.event import Event
    from .toggle_button import ToggleButton
except ImportError:
    from ObservableCollections.observablelist import ObservableList
    from ObservableCollections.observabledict import ObservableDict
    from ObservableCollections.observable import Observable
    from ObservableCollections.event import Event
    from tk_widgets.toggle_button import ToggleButton

class SortableAccordion(tk.Frame):
    '''
    '''

    def __init__(self, parent, skin, *args, **kwargs):
        super().__init__(parent, background=skin.bg_color, *args, **kwargs)
        self.skin = skin
        self.items = ObservableList()
        self.widgets = []
        self.is_repacking = False
        self.placeholder = None
        self.pack_params = dict(side=tk.TOP, fill=tk.BOTH, expand=True)

    def __del__(self):
        ## Any cleanup needed?
        super().__del__()

    def add(self, item, index=None):
        if index is None:
            index = len(self.items)
        item.sa_folded = item.folded.trace('w', lambda _1,_2,_3, self=self, item=item: self.item_onchange(item))

        self.items.insert(index, item)
        self.widgets.insert(index, item)
        item.handle.sa_mousedown = item.handle.bind('<Button-1>', self.item_ondragstart)
        item.handle.sa_mousedrag = item.handle.bind('<B1-Motion>', self.item_ondragmove)
        self._repack()

    def remove_at(self, index):
        item = self.items[index]
        item.handle.unbind('<Button-1>', item.handle.sa_mousedown)
        item.handle.unbind('<B1-Motion>', item.handle.sa_mousedrag)
        item.folded.trace_vdelete('w', item.sa_folded)

        item.destroy()
        del self.items[index]
        del self.widgets[index]
        self._repack()

    def remove(self, item):
        self.remove_at(self.items.index(item))

    def _repack(self):
        self.is_repacking = True

        for widget in self.widgets:
            widget.pack_forget()

        for widget in self.widgets:
            widget.pack(**self.pack_params)

        self.is_repacking = False

    def item_ondragstart(self, event):
        handle = event.widget
        item = handle.item_widget

        item.config(highlightthickness=1, highlightbackground=self.skin.bg_highlight_color)

        self.placeholder = tk.Frame(self, height=item.winfo_height(), width=item.winfo_width(), background='#555555')

        self.dragged_index = self.widgets.index(item)
        self.widgets[self.dragged_index].pack_forget()
        self.widgets[self.dragged_index] = self.placeholder
        self._repack()

        handle.sa_mouseup = handle.bind('<ButtonRelease-1>', self.item_ondragstop)

        item._drag_start_x = event.x
        item._drag_start_y = event.y

        x = item.winfo_x()
        y = item.winfo_y()
        item.place(x=x, y=y, height=item.winfo_height(), width=item.winfo_width())
        item.tkraise()


    def item_ondragmove(self, event):
        if self.is_repacking:
            return

        handle = event.widget
        item = handle.item_widget
        y = item.winfo_y() - item._drag_start_y + event.y

        placeholder_index = self.widgets.index(self.placeholder)
        for i,widget in enumerate(self.widgets):
            wy = widget.winfo_y()
            if y <= wy:
                if i != placeholder_index:
                    self.widgets[placeholder_index] = self.widgets[i]
                    self.widgets[i] = self.placeholder
                    self._repack()
                break
        x = item.winfo_x() - item._drag_start_x + event.x
        y = item.winfo_y() - item._drag_start_y + event.y
        item.place(x=x, y=y, height=item.winfo_height(), width=item.winfo_width())


    def item_ondragstop(self, event):
        handle = event.widget
        item = handle.item_widget

        item.config(highlightthickness=0)

        handle.unbind('<ButtonRelease-1>', handle.sa_mouseup)

        placeholder_index = self.widgets.index(self.placeholder)
        self.widgets[placeholder_index].destroy()
        self.widgets[placeholder_index] = self.items[self.dragged_index]
        self._repack()

        self.items.sort(key=lambda item:self.widgets.index(item))

    def item_onchange(self, item_trigger):
        if item_trigger.folded.get() == False:
            for item in self.items:
                if item != item_trigger:
                    item.folded.set(True)



class AccordionItem(tk.Frame):
    '''
    '''

    def __init__(self, parent, title, skin, *args, index=None, **kwargs):
        '''
        # Arguments:
            - index: position to add the item into (in the parent accordion)
        '''
        super().__init__(parent, bg=skin.bg_color, *args, **kwargs)

        self.skin = skin

        self.header = tk.Frame(self, bg=self.skin.bg_color)
        self.header.pack(side=tk.TOP, fill=tk.X, expand=True)

        drag_image = Path(os.path.dirname(os.path.abspath(__file__))).parent/'resources'/'drag16.png'
        self.drag_image = tk.PhotoImage(file=str(drag_image))
        self.handle = tk.Label(self.header, image=self.drag_image, background=self.skin.bg_color)
        self.handle.pack(side=tk.LEFT)
        self.handle.item_widget = self

        self.title = tk.Label(self.header, text=title, bg=self.skin.bg_color,
                              fg=self.skin.fg_color,anchor=tk.W,
                              font=self.skin.font_heading)
        self.title.pack(side=tk.LEFT)

        self.folded = tk.BooleanVar(value=True)
        self.folded.trace('w', self.fold)
        image_on = Path(os.path.dirname(os.path.abspath(__file__))).parent/'resources'/'arrow_down16.png'
        image_off = Path(os.path.dirname(os.path.abspath(__file__))).parent/'resources'/'arrow_left16.png'
        self.button_fold = ToggleButton(self.header, image_on=image_on, image_off=image_off, variable=self.folded)
        self.button_fold.pack(side=tk.RIGHT, pady=1)

        self.content = tk.Frame(self, bg=self.skin.bg_color)

        parent.add(self, index)

    def fold(self, *args):
        if self.folded.get():
            self.content.pack_forget()
        else:
            self.content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
