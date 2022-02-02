# ------------------------------------------------------------------------------
#  File: view.py
#  Author: Jan Kukacka
#  Date: 3/2021
# ------------------------------------------------------------------------------
#  Main window view
# ------------------------------------------------------------------------------

import os
# import matplotlib
# import matplotlib.colors
# import matplotlib.lines as mlines
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from pathlib import Path
from PIL import ImageTk, Image
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.colorchooser import askcolor as askcolor_
from tkinter.filedialog import askopenfilename as askopenfilename_
from tkinter.filedialog import asksaveasfilename as asksaveasfilename_


import happy as hp
import happy.plots as hpp

try:
    from . import skin as skin_
    from .tk_widgets.limiter import Limiter
    from .tk_widgets.loader_animation import LoaderAnimation
    from .tk_widgets.channels_list import ChannelsList
    from .tk_widgets.window_about import WindowAbout
    from .utils.tk_call_wrapper import CallWrapper
except ImportError:
    import skin as skin_
    from tk_widgets.limiter import Limiter
    from tk_widgets.loader_animation import LoaderAnimation
    from tk_widgets.channels_list import ChannelsList
    from tk_widgets.window_about import WindowAbout
    from utils.tk_call_wrapper import CallWrapper


def set_state(element, state):
    try:
        element.configure(state=state)
    except:
        try:
            ## ttk widgets use different method
            if state == 'disable':
                element.state(['disabled'])
            if state == 'normal':
                element.state(['!disabled'])
        except:
            pass

    for child in element.winfo_children():
        set_state(child, state)


class View(tk.Tk):
    '''
    Main window view class
    '''

    def __init__(self, skin=None, debug=None, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.zoom = 1
        self.offset = (0,0)

        if skin is None:
            skin = skin_.Skin()
        self.skin = skin

        if debug is None:
            debug = False
        if not debug:
            tk.CallWrapper = CallWrapper

        self.window_about = None

        self.setup_mainframe()
        self.setup_menu()
        self.setup_image_axis()
        self.setup_response_panel()
        self.setup_channels_panel()
        self.setup_channels2_panel()
        self.setup_model_io()

        self.loader = LoaderAnimation((self.figure_canvas.winfo_width()/2, 1), self.skin.bg_color, self.figure_canvas, self)

        ## -- bind mouse on canvas
        self.figure_canvas.bind('<Button-1>', self.mouse1_drag)
        self.figure_canvas.bind('<B1-Motion>', self.mouse1_drag)
        self.figure_canvas.bind('<Button-3>', self.mouse2_drag)
        self.figure_canvas.bind('<B3-Motion>', self.mouse2_drag)

        ## -- bind keyboard
        self.bind('+', lambda _,self=self:self.set_zoom(self.zoom+.5))
        self.bind('-', lambda _,self=self:self.set_zoom(self.zoom-.25))
        self.bind('r', self.reset_view)

        self.title('Image Viewer MK II')
        path = Path(os.path.dirname(os.path.abspath(__file__)))
        self.iconbitmap(True, str(path/'resources'/'favicon.ico'))


    def setup_mainframe(self):
        self.mainframe = tk.Frame(self, background=self.skin.bg_color)
        self.mainframe.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        self.grid_frames = []
        for i in range(3):
            frame = tk.Frame(self.mainframe, background=self.skin.bg_color)
            frame.grid(column=i, row=0, sticky='nwes')
            self.grid_frames.append(frame)

    def setup_menu(self):
        self.menu = {'obj': tk.Menu(self.mainframe)}
        self.menu['file'] = {'obj': tk.Menu(self.menu['obj'])}
        self.menu['file']['load_image'] = 'Load image... (Ctrl+O)'
        self.menu['file']['obj'].add_command(label=self.menu['file']['load_image'])
        self.menu['file']['save_render'] = 'Save image... (Ctrl+S)'
        self.menu['file']['obj'].add_command(label=self.menu['file']['save_render'])
        self.menu['file']['load_config'] = 'Load configuration'
        self.menu['file']['obj'].add_command(label=self.menu['file']['load_config'])
        self.menu['file']['save_config'] = 'Save configuration'
        self.menu['file']['obj'].add_command(label=self.menu['file']['save_config'])
        self.menu['obj'].add_cascade(label="File", menu=self.menu['file']['obj'])

        self.menu['image'] = {'obj': tk.Menu(self.menu['obj'])}
        self.menu['image']['transpose'] = 'Transpose (Ctrl+T)'
        self.menu['image']['obj'].add_command(label=self.menu['image']['transpose'])
        self.menu['image']['autocolor'] = 'Default palette'
        self.menu['image']['obj'].add_command(label=self.menu['image']['autocolor'])
        self.menu['obj'].add_cascade(label="Image", menu=self.menu['image']['obj'])

        self.menu['view'] = {'obj': tk.Menu(self.menu['obj'])}
        self.menu['view']['reset'] = 'Reset (R)'
        self.menu['view']['obj'].add_command(label=self.menu['view']['reset'], command=self.reset_view)
        self.menu['view']['zoomin'] = 'Zoom in (+)'
        self.menu['view']['obj'].add_command(label=self.menu['view']['zoomin'], command=lambda self=self:self.set_zoom(self.zoom+.5))
        self.menu['view']['zoomout'] = 'Zoom out (-)'
        self.menu['view']['obj'].add_command(label=self.menu['view']['zoomout'], command=lambda self=self:self.set_zoom(self.zoom-.25))
        self.menu['obj'].add_cascade(label="View", menu=self.menu['view']['obj'])

        self.menu['about'] = 'About'
        self.menu['obj'].add_command(label=self.menu['about'], command=self.open_about)

        tk.Tk.config(self, menu=self.menu['obj'])


    def setup_image_axis(self):
        self.figure_canvas = tk.Canvas(self.grid_frames[0], width=500, height=500, bg=self.skin.bg_color, bd=0, highlightthickness=0)
        self.figure_canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def setup_channels_panel(self):
        self.property_frames = {}
        # self.channel_figures = [None,None]

        self.var_channel = {
            'use_local_contrast': tk.BooleanVar(value=True),
            'local_contrast_neighborhood': tk.IntVar(value=31),
            'local_contrast_cut_off': tk.DoubleVar(value=100),
            'use_gamma': tk.BooleanVar(value=True),
            'gamma': tk.DoubleVar(value=1.0),
            'use_sigmoid': tk.BooleanVar(value=True),
            'sigmoid_low': tk.DoubleVar(value=0),
            'sigmoid_high': tk.DoubleVar(value=100),
            'sigmoid_new_low': tk.DoubleVar(value=0),
            'sigmoid_new_high': tk.DoubleVar(value=100),
            'color': tk.StringVar(value='#000000'),
            'visible': tk.BooleanVar(value=True)
        }

        channel_frame = ttk.LabelFrame(self.grid_frames[2], text='Channel settings', padding=5)
        channel_frame.pack(side=tk.TOP, expand=False, fill=tk.BOTH, padx=5, pady=5)

        self.var_selected_channel = tk.StringVar(value='Channel 0')
        self.channel_combo = ttk.Combobox(channel_frame, state='readonly',
                             textvariable=self.var_selected_channel)
        self.channel_combo.pack(side=tk.TOP, expand=False, fill=tk.X)

        # vis_frame = tk.Frame(channel_frame, bg=self.skin.bg_color)
        # vis_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=0, pady=0)
        #
        #
        # ttk.Checkbutton(vis_frame, text='Visible', variable=self.var_channel['visible'],
        #                 onvalue=True, offvalue=False).pack(side=tk.LEFT, expand=False)
        #
        # self.btn_show_all = ttk.Button(vis_frame, text='Show all')
        # self.btn_show_all.pack(side=tk.RIGHT, expand=False, pady=5)
        # self.btn_hide_all = ttk.Button(vis_frame, text='Hide all')
        # self.btn_hide_all.pack(side=tk.RIGHT, expand=False, padx=5, pady=5)

        color_frame = tk.Frame(channel_frame, bg=self.skin.bg_color)
        color_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=0, pady=5)
        # label = tk.Label(color_frame, text='Color', fg=self.skin.fg_color,
        #                  bg=self.skin.bg_color, anchor=tk.NW)
        # label.pack(side=tk.TOP, expand=False, fill=tk.X)
        grid = tk.Frame(color_frame, bg=self.skin.bg_color)
        grid.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.color_preview = tk.Frame(grid, width=16, height=16, bg=self.var_channel['color'].get())
        self.color_preview.pack(side=tk.LEFT)

        ttk.Entry(grid, textvariable=self.var_channel['color'], width=10).pack(side=tk.LEFT, padx=5)
        path = Path(os.path.dirname(os.path.abspath(__file__)))
        colorpicker = tk.PhotoImage(file=str(path/'resources'/'colorpicker16.png'))
        self.color_picker = ttk.Button(grid, image=colorpicker)
        self.color_picker.image = colorpicker
        self.color_picker.pack(side=tk.LEFT)

        icon = tk.PhotoImage(file=str(path/'resources'/'paste16.png'))
        self.btn_paste = ttk.Button(grid, image=icon)
        self.btn_paste.image = icon
        self.btn_paste.pack(side=tk.RIGHT, padx=3)

        icon = tk.PhotoImage(file=str(path/'resources'/'copy16.png'))
        self.btn_copy = ttk.Button(grid, image=icon)
        self.btn_copy.image = icon
        self.btn_copy.pack(side=tk.RIGHT)

        def setup_slider(parent_frame, title, variable, limit_low, limit_high, resolution):
            slider_frame = tk.Frame(parent_frame, bg=self.skin.bg_color)
            slider_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=0,
                                 pady=0)
            ## Top label
            if title is not None:
                label = tk.Label(slider_frame, text=title, fg=self.skin.fg_color,
                                 bg=self.skin.bg_color, anchor=tk.NW)
                label.pack(side=tk.TOP, expand=False, fill=tk.X)

            ## Pad-x compensates for entry starting too left
            grid = tk.Frame(slider_frame, bg=self.skin.bg_color)
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

        checkbox = ttk.Checkbutton(channel_frame, text='Local contrast enhancement',
                                   variable=self.var_channel['use_local_contrast'],
                                   onvalue=True, offvalue=False)
        checkbox.pack(side=tk.TOP, expand=False, fill=tk.X)
        local_contrast_frame = tk.Frame(channel_frame, background=self.skin.bg_color)
        local_contrast_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=(20,0), pady=0)
        setup_slider(local_contrast_frame, 'Neighborhood size', self.var_channel['local_contrast_neighborhood'], 1, 101, 2)
        setup_slider(local_contrast_frame, 'Normalizer cut-off (% of max)', self.var_channel['local_contrast_cut_off'], 0, 100, 1)
        self.property_frames['use_local_contrast'] = local_contrast_frame

        checkbox = ttk.Checkbutton(channel_frame, text='Sigmoid norm',
                                   variable=self.var_channel['use_sigmoid'],
                                   onvalue=True, offvalue=False)
        checkbox.pack(side=tk.TOP, expand=False, fill=tk.X, pady=(5,0))
        sigmoid_frame = tk.Frame(channel_frame, background=self.skin.bg_color)
        sigmoid_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=(20,0), pady=0)
        setup_slider(sigmoid_frame, 'Lower end', self.var_channel['sigmoid_low'], 0, 100, 0.5)
        setup_slider(sigmoid_frame, 'Upper end', self.var_channel['sigmoid_high'], 0, 100, 0.5)
        setup_slider(sigmoid_frame, 'Sigmoid lower end', self.var_channel['sigmoid_new_low'], 0, 100, 0.5)
        setup_slider(sigmoid_frame, 'Sigmoid upper end', self.var_channel['sigmoid_new_high'], 0, 100, 0.5)
        self.property_frames['use_sigmoid'] = sigmoid_frame

        checkbox = ttk.Checkbutton(channel_frame, text='Gamma correction',
                                   variable=self.var_channel['use_gamma'],
                                   onvalue=True, offvalue=False)
        checkbox.pack(side=tk.TOP, expand=False, fill=tk.X, pady=(5,0))
        gamma_frame = tk.Frame(channel_frame, background=self.skin.bg_color)
        gamma_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=(20,0), pady=0)
        self.property_frames['use_gamma'] = gamma_frame

        setup_slider(gamma_frame, 'Gamma', self.var_channel['gamma'], 0.01, 4, 0.01)


    def setup_channels2_panel(self):
        self.channels_panel = ChannelsList(self.grid_frames[1],self.skin, self.var_selected_channel)


    def setup_response_panel(self):
        frame = ttk.LabelFrame(self.grid_frames[2], text='Channel response', padding=5)
        frame.pack(side=tk.TOP, expand=False, fill=tk.BOTH, padx=5, pady=5)
        self.response_canvas = tk.Canvas(frame, width=128, height=128, bg=self.skin.bg_color, bd=0, highlightthickness=0)
        self.response_canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


    def setup_model_io(self):
        btns_frame = tk.Frame(self.grid_frames[2], bg=self.skin.bg_color)
        btns_frame.pack(side=tk.TOP, pady=5, padx=5, expand=False, fill=tk.X)
        self.btn_save = ttk.Button(btns_frame, text='Save config')
        self.btn_save.pack(side=tk.LEFT, anchor=tk.NE)
        self.btn_load = ttk.Button(btns_frame, text='Load config')
        self.btn_load.pack(side=tk.LEFT, padx=5, anchor=tk.NE)
        self.btn_save_render = ttk.Button(btns_frame, text='Save render')
        self.btn_save_render.pack(side=tk.LEFT, anchor=tk.NE)

    @staticmethod
    def askcolor(initialcolor):
        return askcolor_(initialcolor)[1]

    @staticmethod
    def askopenfilename(*args, **kwargs):
        return askopenfilename_(*args, **kwargs)

    @staticmethod
    def asksaveasfilename(*args,**kwargs):
        return asksaveasfilename_(*args, **kwargs)


    def show_image(self, image=None):
        if image is not None:
            self.image = image

        if self.zoom != 1:
            image = self.image.resize((int(self.image.size[0]*self.zoom),
                                       int(self.image.size[1]*self.zoom)))
        else:
            image = self.image
        self.render_ref = ImageTk.PhotoImage(image)
        # self.figure_canvas.update()
        canvas_width = self.figure_canvas.winfo_width()
        canvas_height = self.figure_canvas.winfo_height()
        # print(canvas_width, canvas_height)
        self.figure_canvas.create_image((canvas_width/2+self.offset[0],canvas_height/2+self.offset[1]), image=self.render_ref)

    def show_response(self, response_image):
        if not response_image is None:
            self.response_ref = ImageTk.PhotoImage(image=Image.fromarray(response_image))
            self.response_canvas.create_image((0,0), image=self.response_ref,anchor=tk.NW)


    def update_channels(self, channel_props):
        self.channel_combo.configure(values=[cp['name'] for cp in channel_props])
        self.channels_panel.recreate_items(channel_props)

    def get_active_channel(self):
        channel_names = [vc['name'].get() for vc in self.channels_panel.var_channels]
        if self.var_selected_channel.get() in channel_names:
            return channel_names.index(self.var_selected_channel.get())
        else:
            return -1

    def mouse1_drag(self, event):
        '''
        Changes image offset
        '''
        if event.type == tk.EventType.Button:
            self.offset_root = (event.x, event.y)
            self.orig_offset = self.offset
        else:
            self.offset = (event.x - self.offset_root[0] + self.orig_offset[0],
                           event.y - self.offset_root[1] + self.orig_offset[1])
            self.show_image()

    def mouse2_drag(self, event):
        '''
        Changes image zoom
        '''
        if event.type == tk.EventType.Button:
            self.orig_zoom = self.zoom
            self.zoom_root = (event.x, event.y)
        else:
            distance = (self.zoom_root[1] - event.y) / 200
            activation = 1 + max(0, distance) + min(0, distance/2)
            self.set_zoom(self.orig_zoom * activation)

    def set_zoom(self, zoom):
        self.zoom = np.maximum(np.minimum(8, zoom),1/2)
        self.show_image()

    def reset_view(self, *args):
        self.zoom = 1
        self.offset = (0,0)
        self.show_image()

    def open_about(self):
        if self.window_about is None:
            self.window_about = WindowAbout(self, self.skin)
            self.window_about.deiconify()
