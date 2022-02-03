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
except ImportError:
    from filters import local_norm
    from filters import sigmoid_norm
    from filters import unsharp_mask

def get_filter_by_name(name):
    '''
    Return type matching given name
    '''
    if name == local_norm.LocalNorm.name:
        return local_norm.LocalNorm
    elif name == sigmoid_norm.SigmoidNorm.name:
        return sigmoid_norm.SigmoidNorm
    elif name == unsharp_mask.UnsharpMask.name:
        return unsharp_mask.UnsharpMask

def get_available_filters():
    return [local_norm.LocalNorm, sigmoid_norm.SigmoidNorm, unsharp_mask.UnsharpMask]
