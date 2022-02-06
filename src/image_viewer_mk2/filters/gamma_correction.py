# ------------------------------------------------------------------------------
#  File: gamma_correction.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Implementation of Gamma correction
# ------------------------------------------------------------------------------

import numpy as np

try:
    from . import filter
except ImportError:
    from filters import filter

class GammaCorrection(filter.Filter):
    '''
    Performs gamma correction (power-law)
    '''

    name = 'gamma_correction'

    def __init__(self, gamma=1):
        '''
        # Arguments:
            - gamma: Power to apply
        '''
        super().__init__()
        self.gamma = gamma

    def __call__(self, img):
        '''
        # Arguments:
            - img: array of data to be normalized

        # Returns:
            - normalized array.
        '''
        result = super().__call__(img)
        if result is not None:
            return result
        else:
            self.cache = self.call(img, self.gamma)
            return self.cache


    @staticmethod
    def call(img, gamma, **kwargs):
        img_min, img_max = img.min(), img.max()

        norm_img = np.power(img, gamma)

        ## Power stays within [0;1] range
        if img_min == 0 and img_max == 1:
            return norm_img
        else:
            norm_min, norm_max = norm_img.min(), norm_img.max()
            scale = (img_max-img_min) / (norm_max-norm_min)
            return img_min + (norm_img-norm_min) * scale


    def serialize(self):
        base_dict = super().serialize()
        base_dict['params']['gamma'] = self.gamma
        return base_dict

    @staticmethod
    def deserialize(serialization):
        gamma = serialization['gamma']
        obj = GammaCorrection(gamma)
        obj._deserialize_parent(serialization)
        return obj
