# ------------------------------------------------------------------------------
#  File: unsharp_mask.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Implementation of Unsharp mask filter
# ------------------------------------------------------------------------------

from scipy.ndimage import gaussian_filter
import happy as hp
import numpy as np

try:
    from . import filter
except ImportError:
    from filters import filter

class UnsharpMask(filter.Filter):
    '''
    Performs unsharp masking
    '''

    name = 'unsharp_mask'

    def __init__(self, strength=1, kernel_size=1):
        '''
        # Arguments:
            - strength: Amount of sharpening / blurring
            - kernel_size: Sigma of the blurring kernel
        '''
        super().__init__()
        self.strength = strength
        self.kernel_size = kernel_size

    def __call__(self, img):
        '''
        # Arguments:
            - img: tensor with the image of shape (channels, height, width)
        # Returns:
            - img: image of the same size as the input img
        '''
        if not self.active:
            return img
        return self.call(img, self.strength, self.kernel_size, self.cutoff_percentile)

    @staticmethod
    def call(img, strength, kernel_size, **kwargs):
        '''
        Taken from development version of scikit-image
        https://github.com/scikit-image/scikit-image/blob/master/skimage/filters/_unsharp_mask.py#L20
        '''
        blurred = gaussian_filter(img, sigma=kernel_size, mode='reflect')
        result = img + (img - blurred) * strength
        return np.clip(result, 0, 1)


    def serialize(self):
        base_dict = super().serialize()
        base_dict['params']['strength'] = self.strength
        base_dict['params']['kernel_size'] = self.kernel_size
        return base_dict

    @staticmethod
    def deserialize(serialization):
        strength = serialization['stream']
        kernel_size = serialization['kernel_size']
        obj = UnsharpMask(strength, kernel_size)
        obj._deserialize_parent(serialization)
        return obj
