# ------------------------------------------------------------------------------
#  File: sigmoid_norm.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Implementation of Sigmoid normalization
# ------------------------------------------------------------------------------

import numpy as np

try:
    from . import filter
except ImportError:
    from filters import filter

class SigmoidNorm(filter.Filter):
    '''
    Performs sigmoid normalization of the given image, by scaling the data
    between given percentiles to range [-1;1], which then sigmoid normalizes to
    "nearly 0" and "nearly 1". Values outside given percentile are squeezed to
    the remaining range.
    '''

    name = 'sigmoid_norm'

    def __init__(self, lower, upper, new_lower, new_upper):
        '''
        # Arguments:
            - lower: percentile between 0 and 100, must be lower than `upper`.
            - upper: percentile between 0 and 100, must be higher than `lower`.
            - new_lower: percentile between 0 and 100, where lower will be mapped on
                the sigmoid curve
            - new_upper: percentile between 0 and 100, where upper will be mapped on
                the sigmoid curve
        '''
        self.lower = lower
        self.upper = upper
        self.new_lower = new_lower
        self.new_upper = new_upper

    def __call__(self, img):
        '''
        # Arguments:
            - img: array of data to be normalized

        # Returns:
            - normalized array.
        '''
        eps = 1e-8

        low = self.lower/100
        high = self.upper/100

        lower = self.new_lower/100
        upper = self.new_upper/100
        new_low = np.log(eps + lower/(1-lower))  # eps to avoid log(0)
        new_high = np.log(upper/(1-upper+eps))   # eps to avoid division by 0
        img = (new_high-new_low) * (img-low)/(high-low+eps) + new_low
        img = 1/(1+np.exp(-img))
        return (img - img.min()) / img.ptp()

    def serialize(self):
        return {'name': self.name,
                'params': {'lower': self.lower,
                           'upper': self.upper,
                           'new_lower': self.new_lower,
                           'new_upper': self.new_upper}}

    @staticmethod
    def deserialize(serialization):
        lower = serialization['lower']
        upper = serialization['upper']
        new_lower = serialization['new_lower']
        new_upper = serialization['new_upper']
        return SigmoidNorm(lower, upper, new_lower, new_upper)