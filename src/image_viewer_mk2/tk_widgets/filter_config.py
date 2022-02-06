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
    from ..utils import event_handler
    from ..utils.tk_lazy_var import BooleanVar, DoubleVar, IntVar
except ImportError:
    from tk_widgets.slider import Slider
    from tk_widgets.link_button import LinkButton
    from utils import event_handler
    from utils.tk_lazy_var import BooleanVar, DoubleVar, IntVar

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
    elif filter_name == 'gamma_correction':
        return GammaCorrectionConfig
    elif filter_name == 'frangi':
        return FrangiConfig
    elif filter_name == 'minmax_norm':
        return MinMaxNormConfig

class FilterConfig(tk.Frame):
    def __init__(self, parent, skin, *args, **kwargs):
        super().__init__(parent, bg=skin.bg_color, *args, **kwargs)

        self.skin = skin
        self.vars = {'active': BooleanVar(value=True)}

        self.source_params = None

        topframe = tk.Frame(self, bg=self.skin.bg_color)
        topframe.pack(side=tk.TOP, expand=False, fill=tk.X)
        ttk.Checkbutton(topframe, text='Active', variable=self.vars['active'],
                        onvalue=True, offvalue=False).pack(side=tk.LEFT)
        self.btn_remove = LinkButton(topframe, text='Remove', skin=self.skin)
        self.btn_remove.pack(side=tk.RIGHT)

        self.config_frame = tk.Frame(self, background=self.skin.bg_color)
        self.config_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=(20,0), pady=0)

    def destroy(self):
        if self.source_params is not None:
            self.source_params.detach(self.source_params_event_handler)
        super().destroy()

    def populate(self, params):
        self.source_params = params
        for key, value in params.items():
            self.vars[key].set(value)
            self.vars[key].trace('w', event_handler.TkVarEventHandler(self.update_source, key=key))
        self.source_params_event_handler = event_handler.ObservableEventHandler(self.on_sourceupdatded)
        self.source_params.attach(self.source_params_event_handler)

    def update_source(self, key):
        self.source_params[key] = self.vars[key].get()

    @event_handler.requires('event')
    def on_sourceupdatded(self, event):
        if event.action == 'itemsUpdated':
            for key, val, _ in event.items:
                if self.vars[key].get() != val:
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

        self.vars['kernel_size'] = DoubleVar(value=10)
        self.vars['cutoff_percentile'] = DoubleVar(value=100)

        self._setup_slider('Radius', self.vars['kernel_size'], 1, 30, 1)
        self._setup_slider('Normalizer cut-off (% of max)', self.vars['cutoff_percentile'], 0, 100, 1)


class SigmoidNormConfig(FilterConfig):
    name = 'sigmoid_norm'
    title = 'Sigmoid norm'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vars['lower'] = DoubleVar(value=0)
        self.vars['upper'] = DoubleVar(value=100)
        self.vars['new_lower'] = DoubleVar(value=0)
        self.vars['new_upper'] = DoubleVar(value=100)

        self._setup_slider('Lower end', self.vars['lower'], 0, 100, 0.5)
        self._setup_slider('Upper end', self.vars['upper'], 0, 100, 0.5)
        self._setup_slider('Sigmoid lower end', self.vars['new_lower'], 0, 100, 0.5)
        self._setup_slider('Sigmoid upper end', self.vars['new_upper'], 0, 100, 0.5)

class UnsharpMaskConfig(FilterConfig):
    name = 'unsharp_mask'
    title = 'Unsharp mask'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vars['kernel_size'] = DoubleVar(value=31)
        self.vars['strength'] = DoubleVar(value=100)

        self._setup_slider('Radius', self.vars['kernel_size'], 0.001, 10, 0.1)
        self._setup_slider('Strength', self.vars['strength'], -10, 10, 0.1)


class GammaCorrectionConfig(FilterConfig):
    name = 'gamma_correction'
    title = 'Gamma correction'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vars['gamma'] = DoubleVar(value=1)
        self._setup_slider('Gamma', self.vars['gamma'], 0.01, 4, 0.01)


class FrangiConfig(FilterConfig):
    name = 'frangi'
    title = 'Frangi filter'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vars['scale_min'] = DoubleVar(value=1)
        self.vars['scale_max'] = DoubleVar(value=10)
        self.vars['scale_step'] = DoubleVar(value=2)
        self.vars['alpha'] = DoubleVar(value=.5)
        self.vars['beta'] = DoubleVar(value=.5)
        self.vars['gamma'] = DoubleVar(value=15)
        self._setup_slider('Sigma min', self.vars['scale_min'], 0.1, 4, 0.1)
        self._setup_slider('Sigma max', self.vars['scale_max'], 0.1, 10, 0.1)
        self._setup_slider('Sigma step', self.vars['scale_step'], 0.1, 4, 0.1)
        self._setup_slider('Alpha', self.vars['alpha'], 0, 1, 0.1)
        self._setup_slider('Beta', self.vars['beta'], 0, 1, 0.1)
        self._setup_slider('Gamma', self.vars['gamma'], 0, 100, 1)

class MinMaxNormConfig(FilterConfig):
    name = 'minmax_norm'
    title = 'Min-Max norm'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vars['in_min'] = DoubleVar(value=0)
        self.vars['in_max'] = DoubleVar(value=1)
        self.vars['out_min'] = DoubleVar(value=0)
        self.vars['out_max'] = DoubleVar(value=1)

        self._setup_slider('Clip min', self.vars['in_min'], 0, 1.01, 0.01)
        self._setup_slider('Clip max', self.vars['in_max'], 0, 1.01, 0.01)
        self._setup_slider('Output min', self.vars['out_min'], 0, 1, 0.01)
        self._setup_slider('Output max', self.vars['out_max'], 0, 1, 0.01)
