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

def prepare_icon(filename, skin):
    path = Path(os.path.dirname(os.path.abspath(__file__)))
    icon = Image.open(str(path/'resources'/filename))
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
        self.channel_variables = []
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

        self.var_channels = []
        for channel_prop in channel_props:
            self.var_channels.append({'color': tk.StringVar(value=channel_prop['color']),
                                      'visible': tk.BooleanVar(value=channel_prop['visible']),
                                      'name': tk.StringVar(value='Channel name')})

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

            color_preview = tk.Frame(frame, width=16, height=16, bg=var_channel['color'].get())
            color_preview.pack(side=tk.LEFT)
            color_preview.bindtags((bind_tag,) + color_preview.bindtags())

            self.wrap_frame.bind_scroll_wheel(color_preview)
            self.color_previews.append(color_preview)
            var_channel['color'].trace('w', lambda _1,_2,_3, obj=color_preview, var=var_channel['color']: obj.config(background=str(var.get())))

            label = tk.Label(frame, textvariable=var_channel['name'], fg=self.skin.fg_color,
                             bg=self.skin.bg_color, anchor=tk.NW)
            label.pack(side=tk.LEFT, pady=2, padx=3)
            label.bindtags((bind_tag,) + label.bindtags())
            frame.label = label
            self.wrap_frame.bind_scroll_wheel(label)

            frame.bind_class(bind_tag, '<Button-1>', lambda e: self.channel_onselect(e, var_channel['name'].get()))
            frame.bind_class(bind_tag, '<Double-Button-1>', lambda _, channel_index=channel_index: self.init_rename_channel(channel_index))

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
        handler = lambda _, frame=frame, entry=entry, channel_index=channel_index: self.end_rename_channel(frame, entry, channel_index)
        entry.bind('<FocusOut>', handler)
        entry.bind('<Return>', handler)
        entry.bind('<Escape>', lambda _, frame=frame, entry=entry: self.cancel_rename_channel(frame, entry))

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

    def channel_onselect(self, event, channel_name):
        event.widget.focus_set()
        self.var_selected_channel.set(channel_name)

    def highlight_item(self, item_index):
        for frame in self.item_frames:
            frame.config(bg=self.skin.bg_color)
            frame.checkbox.configure(style='TCheckbutton')
            frame.label.config(bg=self.skin.bg_color)
        self.item_frames[item_index].config(bg=self.skin.bg_highlight_color)
        self.item_frames[item_index].checkbox.configure(style='Highlight.TCheckbutton')
        self.item_frames[item_index].label.config(bg=self.skin.bg_highlight_color)


"""Implementation of the scrollable frame widget."""

import sys

try:
    # Python 3
    import tkinter as tk
except (ImportError):
    # Python 2
    import Tkinter as tk

try:
    try:
        # Python 3
        import tkinter.ttk as ttk
    except (ImportError):
        # Python 2
        import ttk
except (ImportError):
    # Can't provide ttk's Scrollbar
    pass


# __all__ = ["ScrolledFrame"]


class ScrolledFrame(tk.Frame):
    """Scrollable Frame widget.

    Use display_widget() to set the interior widget. For example,
    to display a Label with the text "Hello, world!", you can say:

        sf = ScrolledFrame(self)
        sf.pack()
        sf.display_widget(Label, text="Hello, world!")

    The constructor accepts the usual Tkinter keyword arguments, plus
    a handful of its own:

      scrollbars (str; default: "both")
        Which scrollbars to provide.
        Must be one of "vertical", "horizontal," "both", or "neither".

      use_ttk (bool; default: False)
        Whether to use ttk widgets if available.
        The default is to use standard Tk widgets. This setting has
        no effect if ttk is not available on your system.
    """

    def __init__(self, master=None, **kw):
        """Return a new scrollable frame widget."""

        tk.Frame.__init__(self, master)

        # Hold these names for the interior widget
        self._interior = None
        self._interior_id = None

        # Whether to fit the interior widget's width to the canvas
        self._fit_width = False

        # Which scrollbars to provide
        if "scrollbars" in kw:
            scrollbars = kw["scrollbars"]
            del kw["scrollbars"]

            if not scrollbars:
                scrollbars = self._DEFAULT_SCROLLBARS
            elif not scrollbars in self._VALID_SCROLLBARS:
                raise ValueError("scrollbars parameter must be one of "
                                 "'vertical', 'horizontal', 'both', or "
                                 "'neither'")
        else:
            scrollbars = self._DEFAULT_SCROLLBARS

        # Whether to use ttk widgets if available
        if "use_ttk" in kw:
            if ttk and kw["use_ttk"]:
                Scrollbar = ttk.Scrollbar
            else:
                Scrollbar = tk.Scrollbar
            del kw["use_ttk"]
        else:
            Scrollbar = tk.Scrollbar

        # Default to a 1px sunken border
        if not "borderwidth" in kw:
            kw["borderwidth"] = 1
        if not "relief" in kw:
            kw["relief"] = "sunken"

        # Set up the grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Canvas to hold the interior widget
        c = self._canvas = tk.Canvas(self,
                                     borderwidth=0,
                                     highlightthickness=0,
                                     takefocus=0)

        # Enable scrolling when the canvas has the focus
        self.bind_arrow_keys(c)
        self.bind_scroll_wheel(c)

        # Call _resize_interior() when the canvas widget is updated
        c.bind("<Configure>", self._resize_interior)

        # Scrollbars
        xs = self._x_scrollbar = Scrollbar(self,
                                           orient="horizontal",
                                           command=c.xview)
        ys = self._y_scrollbar = Scrollbar(self,
                                           orient="vertical",
                                           command=c.yview)
        c.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)

        # Lay out our widgets
        c.grid(row=0, column=0, sticky="nsew")
        if scrollbars == "vertical" or scrollbars == "both":
            ys.grid(row=0, column=1, sticky="ns")
        if scrollbars == "horizontal" or scrollbars == "both":
            xs.grid(row=1, column=0, sticky="we")

        # Forward these to the canvas widget
        self.bind = c.bind
        self.focus_set = c.focus_set
        self.unbind = c.unbind
        self.xview = c.xview
        self.xview_moveto = c.xview_moveto
        self.yview = c.yview
        self.yview_moveto = c.yview_moveto

        # Process our remaining configuration options
        self.configure(**kw)

    def __setitem__(self, key, value):
        """Configure resources of a widget."""

        if key in self._CANVAS_KEYS:
            # Forward these to the canvas widget
            self._canvas.configure(**{key: value})

        else:
            # Handle everything else normally
            tk.Frame.configure(self, **{key: value})

    # ------------------------------------------------------------------------

    def bind_arrow_keys(self, widget):
        """Bind the specified widget's arrow key events to the canvas."""

        widget.bind("<Up>",
                    lambda event: self._canvas.yview_scroll(-1, "units"))

        widget.bind("<Down>",
                    lambda event: self._canvas.yview_scroll(1, "units"))

        widget.bind("<Left>",
                    lambda event: self._canvas.xview_scroll(-1, "units"))

        widget.bind("<Right>",
                    lambda event: self._canvas.xview_scroll(1, "units"))

    def bind_scroll_wheel(self, widget):
        """Bind the specified widget's mouse scroll event to the canvas."""

        widget.bind("<MouseWheel>", self._scroll_canvas)
        widget.bind("<Button-4>", self._scroll_canvas)
        widget.bind("<Button-5>", self._scroll_canvas)

    def cget(self, key):
        """Return the resource value for a KEY given as string."""

        if key in self._CANVAS_KEYS:
            return self._canvas.cget(key)

        else:
            return tk.Frame.cget(self, key)

    # Also override this alias for cget()
    __getitem__ = cget

    def configure(self, cnf=None, **kw):
        """Configure resources of a widget."""

        # This is overridden so we can use our custom __setitem__()
        # to pass certain options directly to the canvas.
        if cnf:
            for key in cnf:
                self[key] = cnf[key]

        for key in kw:
            self[key] = kw[key]

    # Also override this alias for configure()
    config = configure

    def display_widget(self, widget_class, fit_width=False, **kw):
        """Create and display a new widget.

        If fit_width == True, the interior widget will be stretched as
        needed to fit the width of the frame.

        Keyword arguments are passed to the widget_class constructor.

        Returns the new widget.
        """

        # Blank the canvas
        self.erase()

        # Set width fitting
        self._fit_width = fit_width

        # Set the new interior widget
        self._interior = widget_class(self._canvas, **kw)

        # Add the interior widget to the canvas, and save its widget ID
        # for use in _resize_interior()
        self._interior_id = self._canvas.create_window(0, 0,
                                                       anchor="nw",
                                                       window=self._interior)

        # Call _update_scroll_region() when the interior widget is resized
        self._interior.bind("<Configure>", self._update_scroll_region)

        # Fit the interior widget to the canvas if requested
        # We don't need to check fit_width here since _resize_interior()
        # already does.
        self._resize_interior()

        # Scroll to the top-left corner of the canvas
        self.scroll_to_top()

        return self._interior

    def erase(self):
        """Erase the displayed widget."""

        # Clear the canvas
        self._canvas.delete("all")

        # Delete the interior widget
        del self._interior
        del self._interior_id

        # Save these names
        self._interior = None
        self._interior_id = None

        # Reset width fitting
        self._fit_width = False

    def scroll_to_top(self):
        """Scroll to the top-left corner of the canvas."""

        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)

    # ------------------------------------------------------------------------

    def _resize_interior(self, event=None):
        """Resize the interior widget to fit the canvas."""

        if self._fit_width and self._interior_id:
            # The current width of the canvas
            canvas_width = self._canvas.winfo_width()

            # The interior widget's requested width
            requested_width = self._interior.winfo_reqwidth()

            if requested_width != canvas_width:
                # Resize the interior widget
                new_width = max(canvas_width, requested_width)
                self._canvas.itemconfigure(self._interior_id, width=new_width)

    def _scroll_canvas(self, event):
        """Scroll the canvas."""

        c = self._canvas

        if sys.platform.startswith("darwin"):
            # macOS
            c.yview_scroll(-1 * event.delta, "units")

        elif event.num == 4:
            # Unix - scroll up
            c.yview_scroll(-1, "units")

        elif event.num == 5:
            # Unix - scroll down
            c.yview_scroll(1, "units")

        else:
            # Windows
            c.yview_scroll(-1 * (event.delta // 120), "units")

    def _update_scroll_region(self, event):
        """Update the scroll region when the interior widget is resized."""

        # The interior widget's requested width and height
        req_width = self._interior.winfo_reqwidth()
        req_height = self._interior.winfo_reqheight()

        # Set the scroll region to fit the interior widget
        self._canvas.configure(scrollregion=(0, 0, req_width, req_height))

    # ------------------------------------------------------------------------

    # Keys for configure() to forward to the canvas widget
    _CANVAS_KEYS = "width", "height", "takefocus", "bg"

    # Scrollbar-related configuration
    _DEFAULT_SCROLLBARS = "both"
    _VALID_SCROLLBARS = "vertical", "horizontal", "both", "neither"
