# ------------------------------------------------------------------------------
#  File: filter_factory.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Filter factory
# ------------------------------------------------------------------------------

try:
    from . import local_norm
    from . import sigmoid_norm
    from . import unsharp_mask
    from . import gamma_correction
    from . import frangi
    from . import minmax_norm
except ImportError:
    from filters import local_norm
    from filters import sigmoid_norm
    from filters import unsharp_mask
    from filters import gamma_correction
    from filters import frangi
    from filters import minmax_norm

__available_filters = (local_norm.LocalNorm,
                       sigmoid_norm.SigmoidNorm,
                       unsharp_mask.UnsharpMask,
                       gamma_correction.GammaCorrection,
                       frangi.Frangi,
                       minmax_norm.MinMaxNorm)

def get_filter_by_name(name):
    '''
    Return type matching given name
    '''
    for T_filter in __available_filters:
        if name == T_filter.name:
            return T_filter

def get_available_filters():
    return __available_filters
