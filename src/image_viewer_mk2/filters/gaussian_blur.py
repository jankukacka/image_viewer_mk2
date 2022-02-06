# ------------------------------------------------------------------------------
#  File: gaussian_blur.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Implementation of Gaussian blur
# ------------------------------------------------------------------------------

import numpy as np
from skimage.filters import gaussian

try:
    from . import filter
except ImportError:
    from filters import filter

class GaussianBlur(filter.Filter):
    '''
    Performs gaussian blur
    '''

    name = 'gaussian_blur'

    def __init__(self, sigma=1):
        '''
        # Arguments:
            - sigma: Std. deviation of the gaussian kernel
        '''
        super().__init__()
        self.sigma = sigma

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
            self.cache = self.call(img, self.sigma)
            return self.cache


    @staticmethod
    def call(img, sigma, **kwargs):
        img_min, img_max = img.min(), img.max()

        norm_img = gaussian(img, sigma, preserve_range=True)

        norm_min, norm_max = norm_img.min(), norm_img.max()
        scale = (img_max-img_min) / (norm_max-norm_min)
        return img_min + (norm_img-norm_min) * scale
        return norm_img

    def serialize(self):
        base_dict = super().serialize()
        base_dict['params']['sigma'] = self.sigma
        return base_dict

    @staticmethod
    def deserialize(serialization):
        sigma = serialization['sigma']
        obj = GaussianBlur(sigma)
        obj._deserialize_parent(serialization)
        return obj
