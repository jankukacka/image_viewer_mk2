# ------------------------------------------------------------------------------
#  File: local_norm.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Implementation of Local contrast normalizatio
# ------------------------------------------------------------------------------

from scipy.ndimage import gaussian_filter
import happy as hp
import numpy as np

try:
    from . import filter
except ImportError:
    from filters import filter

class LocalNorm(filter.Filter):
    '''
    Performs local normalization of a given image relative to the neighborhood
    of size (kernel_size, kernel_size)  using a global cutoffself.
    '''

    name = 'local_norm'

    def __init__(self, cutoff_percentile=80, kernel_size=10):
        '''
        # Arguments:
            - kernel_size: sigma of the gaussian kernel.
            - cutoff_percentile: int between 0 and 100. Global percentile cut-off,
                preventing over-amplification of noise.
        '''
        super().__init__()
        self.cutoff_percentile = cutoff_percentile
        self.kernel_size = kernel_size

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
            self.cache = self.call(img, self.kernel_size, self.cutoff_percentile)
            return self.cache

    @staticmethod
    def call(img, kernel_size, cutoff_percentile, **kwargs):
        ## Compute input range
        img_min, img_max = img.min(), img.max()

        norm = gaussian_filter(img, kernel_size)
        cutoff = np.max(norm) * np.power(cutoff_percentile/100, 3)
        norm_img = img / np.maximum(norm, cutoff)
        norm_img = np.nan_to_num(norm_img)

        ## Ensure norm_img has same scale as input to enable averaging
        norm_min, norm_max = norm_img.min(), norm_img.max()
        scale = (img_max-img_min)/(norm_max-norm_min)
        norm_img = img_min + (norm_img-norm_min)*scale
        result = img+norm_img

        ## Ensure output has same range as input
        res_min, res_max = result.min(), result.max()
        scale = (img_max-img_min)/(res_max-res_min)
        result = img_min + (result-res_min)*scale

        return result


    def serialize(self):
        base_dict = super().serialize()
        base_dict['params']['cutoff_percentile'] = self.cutoff_percentile
        base_dict['params']['kernel_size'] = self.kernel_size
        return base_dict

    @staticmethod
    def deserialize(serialization):
        cutoff_percentile = serialization['cutoff_percentile']
        kernel_size = serialization['kernel_size']
        obj = LocalNorm(cutoff_percentile, kernel_size)
        obj._deserialize_parent(serialization)
        return obj
