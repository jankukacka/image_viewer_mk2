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

    def __init__(self, cutoff_percentile, kernel_size):
        '''
        # Arguments:
            - kernel_size: size of the averaging kernel or tuple of (kernel_height,
                kernel_width). Should be odd ints.
            - cutoff_percentile: int between 0 and 100. Global percentile cut-off,
                preventing over-amplification of noise.
        '''
        self.cutoff_percentile = cutoff_percentile
        self.kernel_size = kernel_size
        super().__init__()

    def __call__(self, img):
        '''
        # Arguments:
            - img: tensor with the image of shape (channels, height, width)
        # Returns:
            - norm_img: image of the same size as the input img, with values
                locally normalized.
        '''
        kernel_size = hp.misc.ensure_list(self.kernel_size)
        if len(kernel_size) == 1:
            kernel_size = (kernel_size[0], kernel_size[0])

        norm = gaussian_filter(img, [k/3 for k in kernel_size])
        cutoff = np.max(norm) * np.power(self.cutoff_percentile/100, 3)
        norm_img = img / np.maximum(norm, cutoff)
        norm_img = np.nan_to_num(norm_img)

        img = (img-img.min())/img.ptp()
        norm_img = (norm_img-norm_img.min())/norm_img.ptp()

        return (img+norm_img)/2

    def serialize(self):
        return {'name': self.name,
                'params': {'cutoff_percentile': self.cutoff_percentile,
                           'kernel_size': self.kernel_size}}

    @staticmethod
    def deserialize(serialization):
        cutoff_percentile = serialization['cutoff_percentile']
        kernel_size = serialization['kernel_size']
        return LocalNorm(cutoff_percentile, kernel_size)
