# ------------------------------------------------------------------------------
#  File: minmax_norm.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Implementation of Min-Max normalization
# ------------------------------------------------------------------------------

from scipy.ndimage import gaussian_filter
import happy as hp
import numpy as np

try:
    from . import filter
except ImportError:
    from filters import filter

class MinMaxNorm(filter.Filter):
    '''
    Adjusts the minimum and maximum of the image
    '''

    name = 'minmax_norm'

    def __init__(self, in_min=0, in_max=1, out_min=0, out_max=1):
        '''
        # Arguments:
            - in_min, in_max: floats. Define saturation levels.
            - out_min, out_max: floats. Define output range.
        '''
        super().__init__()
        self.in_min = in_min
        self.in_max = in_max
        self.out_min = out_min
        self.out_max = out_max

    def __call__(self, img):
        '''
        # Arguments:
            - img: tensor with the image of shape (channels, height, width)
        # Returns:
            - norm_img: image of the same size as the input img, with values
                locally normalized.
        '''
        result = super().__call__(img)
        if result is not None:
            return result
        else:
            self.cache = self.call(img, self.in_min, self.in_max, self.out_min, self.out_max)
            return self.cache

    @staticmethod
    def call(img, in_min, in_max, out_min, out_max, **kwargs):
        ## Compute input range
        img = np.clip(img, a_min=in_min, a_max=in_max)


        scale = (out_max-out_min)/(in_max-in_min)
        result = out_min + (img-in_min)*scale

        return result


    def serialize(self):
        base_dict = super().serialize()
        base_dict['params']['in_min'] = self.in_min
        base_dict['params']['in_max'] = self.in_max
        base_dict['params']['out_min'] = self.out_min
        base_dict['params']['out_max'] = self.out_max
        return base_dict

    @staticmethod
    def deserialize(serialization):
        in_min = serialization['in_min']
        in_max = serialization['in_max']
        out_min = serialization['out_min']
        out_max = serialization['out_max']
        obj = MinMaxNorm(in_min, in_max, out_min, out_max)
        obj._deserialize_parent(serialization)
        return obj
