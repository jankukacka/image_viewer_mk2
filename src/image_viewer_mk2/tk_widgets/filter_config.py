# ------------------------------------------------------------------------------
#  File: filter_config.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Widget for displaying filter configuration
# ------------------------------------------------------------------------------

import tkinter as tk
import tkinter.ttk as ttk

try:
    from .slider import Slider
    from .link_button import LinkButton
except ImportError:
    from tk_widgets.slider import Slider
    from tk_widgets.link_button import LinkButton

def get_filter_widget(filter_name):
    '''
    For a given filter name, returns the corresponding filter widget class
    '''
    if filter_name == 'local_norm':
        return LocalNormConfig
    elif filter_name == 'sigmoid_norm':
        return SigmoidNormConfig
    elif filter_name == 'unsharp_mask':
        return UnsharpMaskConfig

class FilterConfig(tk.Frame):
    def __init__(self, parent, skin, *args, **kwargs):
        super().__init__(parent, bg=skin.bg_color, *args, **kwargs)

        self.skin = skin
        self.vars = {'active': tk.BooleanVar(value=True)}

        topframe = tk.Frame(self, bg=self.skin.bg_color)
        topframe.pack(side=tk.TOP, expand=False, fill=tk.X)
        ttk.Checkbutton(topframe, text='Active', variable=self.vars['active'],
                        onvalue=True, offvalue=False).pack(side=tk.LEFT)
        self.btn_remove = LinkButton(topframe, text='Remove', skin=self.skin)
        self.btn_remove.pack(side=tk.RIGHT)

        self.config_frame = tk.Frame(self, background=self.skin.bg_color)
        self.config_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=(20,0), pady=0)

    def populate(self, params):
        for key, value in params.items():
            self.vars[key].set(value)
            self.vars[key].trace('w', lambda _1,_2,_3,p=params,k=key,self=self: self.update_source(p,k))
        params.attach(self.on_sourceupdatded)

    def update_source(self, params, key):
        params[key] = self.vars[key].get()

    def on_sourceupdatded(self, event):
        if event.action == 'itemsUpdated':
            for key, val, _ in event.items:
                self.vars[key].set(val)

    def _setup_slider(self, title, variable, limit_low, limit_high, resolution):
        slider = Slider(self.config_frame, title, variable, limit_low,
                        limit_high, resolution, skin=self.skin)
        slider.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=0, pady=0)



class LocalNormConfig(FilterConfig):
    name = 'local_norm'
    title = 'Local contrast normalization'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vars['kernel_size'] = tk.IntVar(value=31)
        self.vars['cutoff_percentile'] = tk.DoubleVar(value=100)

        self._setup_slider('Radius', self.vars['kernel_size'], 1, 101, 2)
        self._setup_slider('Normalizer cut-off (% of max)', self.vars['cutoff_percentile'], 0, 100, 1)


class SigmoidNormConfig(FilterConfig):
    name = 'sigmoid_norm'
    title = 'Sigmoid norm'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vars['lower'] = tk.DoubleVar(value=0)
        self.vars['upper'] = tk.DoubleVar(value=100)
        self.vars['new_lower'] = tk.DoubleVar(value=0)
        self.vars['new_upper'] = tk.DoubleVar(value=100)

        self._setup_slider('Lower end', self.vars['lower'], 0, 100, 0.5)
        self._setup_slider('Upper end', self.vars['upper'], 0, 100, 0.5)
        self._setup_slider('Sigmoid lower end', self.vars['new_lower'], 0, 100, 0.5)
        self._setup_slider('Sigmoid upper end', self.vars['new_upper'], 0, 100, 0.5)

class UnsharpMaskConfig(FilterConfig):
    name = 'unsharp_mask'
    title = 'Unsharp mask'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vars['kernel_size'] = tk.DoubleVar(value=31)
        self.vars['strength'] = tk.DoubleVar(value=100)

        self._setup_slider('Radius', self.vars['kernel_size'], 0.001, 10, 0.1)
        self._setup_slider('Strength', self.vars['strength'], -10, 10, 0.1)
