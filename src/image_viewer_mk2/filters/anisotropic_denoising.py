# ------------------------------------------------------------------------------
#  File: anisotropic_denoising.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Implementation of anisotropic denoising
#  Based on code by Alistair Muldal (c) 2012
#      - source: https://pastebin.com/sBsPX4Y7
# ------------------------------------------------------------------------------

import numpy as np

try:
    from . import filter
except ImportError:
    from filters import filter

class AnisotropicDenoising(filter.Filter):
    '''

    '''

    name = 'anisotropic_denoising'

    def __init__(self, step_size=.15, sensitivity=.1, n_iter=10):
        '''
        # Arguments:
            - step_size:
            - sensitivity:
            - n_iter:
        '''
        super().__init__()
        self.step_size = step_size
        self.sensitivity = sensitivity
        self.n_iter = n_iter

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
            self.cache = self.call(img, self.step_size, self.sensitivity, self.n_iter)
            return self.cache


    @staticmethod
    def call(img, step_size, sensitivity, n_iter, **kwargs):
        img_min, img_max = img.min(), img.max()

        norm_img = anisodiff(img, step_size, sensitivity, n_iter)

        norm_min, norm_max = norm_img.min(), norm_img.max()
        scale = (img_max-img_min) / (norm_max-norm_min)
        return img_min + (norm_img-norm_min) * scale


    def serialize(self):
        base_dict = super().serialize()
        base_dict['params']['step_size'] = self.step_size
        base_dict['params']['sensitivity'] = self.sensitivity
        base_dict['params']['n_iter'] = self.n_iter
        return base_dict

    @staticmethod
    def deserialize(serialization):
        step_size = serialization['step_size']
        sensitivity = serialization['sensitivity']
        n_iter = serialization['n_iter']
        obj = AnisotropicDenoising(step_size, sensitivity, n_iter)
        obj._deserialize_parent(serialization)
        return obj

# ------------------------------------------------------------------------------
#  Based on code by Alistair Muldal (c) 2012
#      - source: https://pastebin.com/sBsPX4Y7

# Original work: Copyright (c) 1995-2012 Peter Kovesi pk@peterkovesi.com
# Modified work: Copyright (c) 2012 Alistair Muldal
# Modified work: Copyright (c) 2022 Jan Kukacka
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose and noninfringement. In no event shall the
# authors or copyright holders be liable for any claim, damages or other
# liability, whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other dealings in the
# software.

from scipy.ndimage import gaussian_filter

def anisodiff(img, gamma=0.1, kappa=50, niter=1, sigma=0, option=1):
    """
    Anisotropic diffusion.

    Usage:
    imgout = anisodiff(im, niter, kappa, gamma, option)

    Arguments:
            img    - input image
            gamma  - max value of .25 for stability
            kappa  - conduction coefficient 20-100 ?
            niter  - number of iterations
            step   - tuple, the distance between adjacent pixels in (y,x)
            option - 1 Perona Malik diffusion equation No 1
                     2 Perona Malik diffusion equation No 2

    Returns:
            imgout   - diffused image.

    kappa controls conduction as a function of gradient.  If kappa is low
    small intensity gradients are able to block conduction and hence diffusion
    across step edges.  A large value reduces the influence of intensity
    gradients on conduction.

    gamma controls speed of diffusion (you usually want it at a maximum of
    0.25)

    Diffusion equation 1 favours high contrast edges over low contrast ones.
    Diffusion equation 2 favours wide regions over smaller ones.
    """

    # initialize output array
    imgout = img.copy()

    # initialize some internal variables
    deltaS = np.zeros_like(imgout)
    deltaE = deltaS.copy()
    NS = deltaS.copy()
    EW = deltaS.copy()
    gS = np.ones_like(imgout)
    gE = gS.copy()

    for ii in np.arange(1,niter):

        # calculate the diffs
        deltaS[:-1,: ] = np.diff(imgout,axis=0)
        deltaE[: ,:-1] = np.diff(imgout,axis=1)

        if sigma > 0:
            deltaSf=gaussian_filter(deltaS,sigma)
            deltaEf=gaussian_filter(deltaE,sigma)
        else:
            deltaSf=deltaS
            deltaEf=deltaE

        # conduction gradients (only need to compute one per dim!)
        if option == 1:
            gS = np.exp(-(deltaSf/kappa)**2.)
            gE = np.exp(-(deltaEf/kappa)**2.)
        elif option == 2:
            gS = 1./(1.+(deltaSf/kappa)**2.)
            gE = 1./(1.+(deltaEf/kappa)**2.)

        # update matrices
        E = gE*deltaE
        S = gS*deltaS

        # subtract a copy that has been shifted 'North/West' by one
        # pixel. don't as questions. just do it. trust me.
        NS[:] = S
        EW[:] = E
        NS[1:,:] -= S[:-1,:]
        EW[:,1:] -= E[:,:-1]

        # update the image
        imgout += gamma*(NS+EW)

    return imgout

# ------------------------------------------------------------------------------
