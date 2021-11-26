# ------------------------------------------------------------------------------
#  File: app.py
#  Author: Jan Kukacka
#  Date: 3/2021
# ------------------------------------------------------------------------------
#  App interface - processes inputs, starts GUI, returns output
# ------------------------------------------------------------------------------

import numpy as np
import happy as hp
try:
    from . import view as view_
    from . import model as model_
    from . import presenter as presenter_
except ImportError:
    import view as view_
    import model as model_
    import presenter as presenter_


def start(file=None, image=None, **kwargs):
    '''
    Starts the app and opens optionally given file or uses given image.

    # Arguments:
    - file: Optional. Filename to open
    - image: Optional. Alternatively, an opened image can be passed as an array
        of shape (height, width, n_channels)

    # Additional optional kwargs:
    - gpu: bool. If True, PyTorch+GPU based rendering will be used (if
        installed). If False (default), defaults to NumPy+CPU rendering
    - config_filename: Filename of the config to apply.
    - config: Dictionary with config to apply.
    - return_config: bool. If True, returns also the config dict. False by default.

    # Returns
    - rendered image as numpy array (height, width, RGBA)
    - (config dictionary. Only if return_config was set to True.)
    '''

    model_kwargs = {'use_gpu': False}
    if 'gpu' in kwargs:
        model_kwargs['use_gpu'] = kwargs['gpu']

    config = None
    if 'config_filename' in kwargs:
        config = hp.io.load(kwargs['config_filename'])
    if 'config' in kwargs:
        config = kwargs['config']

    view_kwargs = {}
    if 'debug' in kwargs:
        view_kwargs['debug'] = kwargs['debug']
        model_kwargs['debug'] = kwargs['debug']

    return_config = False
    if 'return_config' in kwargs:
        return_config = kwargs['return_config']

    view = view_.View(**view_kwargs)
    with model_.Model(**model_kwargs) as model:
        presenter = presenter_.Presenter(view, model)

        if image is not None:
            model.update_image(image)

        if file is not None:
            model.filename = file

            ## Model loading has to wait for image loading io to finish
            def img_onload(event):
                if event.action == 'propertyChanged' and event.propertyName == 'render':
                    if config is not None:
                        model.load(config)
                    view.after(1, lambda: model.detach(img_onload))
            model.attach(img_onload)

        presenter.mainloop()
        result = np.array(model.render)
        config = model.save()

    if return_config:
        return result, config
    else:
        return result
