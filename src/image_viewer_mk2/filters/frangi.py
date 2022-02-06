# ------------------------------------------------------------------------------
#  File: frangi.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Implementation of Vesselness filter
# ------------------------------------------------------------------------------

import numpy as np
from skimage.filters import frangi, meijering

try:
    from . import filter
except ImportError:
    from filters import filter

class Frangi(filter.Filter):
    '''
    Applies Frangi filter
    '''

    name = 'frangi'

    def __init__(self, scale_min=1, scale_max=10, scale_step=2, alpha=0.5, beta=.5, gamma=15):
        '''
        # Arguments:
            - see parameters of skimage.filters.frangi.
        '''
        super().__init__()
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.scale_step = scale_step
        self.alpha = alpha
        self.beta = beta
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
            self.cache = self.call(img, self.scale_min, self.scale_max, self.scale_step, self.alpha, self.beta, self.gamma)
            return self.cache


    @staticmethod
    def call(img, scale_min, scale_max, scale_step, alpha, beta, gamma, **kwargs):
        img_min, img_max = img.min(), img.max()

        sigmas = np.arange(min(scale_min, scale_max), max(scale_min, scale_max), scale_step)
        # norm_img = frangi(img, sigmas=sigmas, alpha=alpha, beta=beta, gamma=gamma, black_ridges=False)
        norm_img = meijering(img, sigmas=sigmas, alpha=alpha, black_ridges=False)

        norm_min, norm_max = norm_img.min(), norm_img.max()
        scale = (img_max-img_min) / (norm_max-norm_min)
        return img_min + (norm_img-norm_min) * scale


    def serialize(self):
        base_dict = super().serialize()
        base_dict['params']['scale_min'] = self.scale_min
        base_dict['params']['scale_max'] = self.scale_max
        base_dict['params']['scale_step'] = self.scale_step
        base_dict['params']['alpha'] = self.alpha
        base_dict['params']['beta'] = self.beta
        base_dict['params']['gamma'] = self.gamma
        return base_dict

    @staticmethod
    def deserialize(serialization):
        scale_min = serialization['scale_min']
        scale_max = serialization['scale_max']
        scale_step = serialization['scale_step']
        alpha = serialization['alpha']
        beta = serialization['beta']
        gamma = serialization['gamma']
        obj = Frangi(scale_min, scale_max, scale_step, alpha, beta, gamma)
        obj._deserialize_parent(serialization)
        return obj
