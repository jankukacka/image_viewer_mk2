# ------------------------------------------------------------------------------
#  File: get_2d_cmap.py
#  Author: Jan Kukacka
#  Date: 11/2019
# ------------------------------------------------------------------------------
#  Script for generation of 2d colormaps
# ------------------------------------------------------------------------------

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scipy.spatial
import scipy.special
import skimage.color as sc
from colormath.color_objects import sRGBColor, LCHuvColor
from colormath.color_conversions import convert_color


def get_coefficients(coordinates):
    '''
    Given coordinates of data in the 2D space [0,1]x[0,1], computes the
    coefficients w.r.t. its edges.

    # Arguments:
        - coordinates: array of shape (n_coords, 2)

    # Returns:
        - coefficients: array of shape (n_coords, 4), corresponding to
            coefficients w.r.t. edges [0,0], [1,0], [0,1], [1,1]
    '''
    ## homogenize coordinates
    n_points = coordinates.shape[0]
    coordinates = np.concatenate([coordinates, np.ones((n_points,1))], axis=-1)

    ## coordinates of vertices of upper and lower triangles
    t1 = np.array([[0,0,1], [1,0,1], [1,1,1]]).T
    t2 = np.array([[0,0,1], [0,1,1], [1,1,1]]).T

    ## barycentric coordinates (~coefficients) w.r.t upper and lower triangles
    bc1 = np.linalg.solve(t1,coordinates.T).T
    bc2 = np.linalg.solve(t2,coordinates.T).T

    mask = coordinates[:,0] > coordinates[:,1]
    coefficients = np.zeros((n_points, 4))

    mask_idx = np.nonzero(mask)[0]
    mask_neg_idx = np.nonzero(np.logical_not(mask))[0]

    coefficients[np.ix_(mask_neg_idx, [0,2,3])] = bc2[np.logical_not(mask)]
    coefficients[np.ix_(mask_idx, [0,1,3])] = bc1[mask]

    return coefficients


def rgb2cs(colors, cs):
    '''
    Coverts array of colors to a color space cs

    # Arguments:
        - colors: array of RGB colors, shape (n_colors, 3)
        - cs: 'RGB', 'LAB', 'LCHab', 'LCHuv', 'XYZ', 'HSV'

    # Returns:
        - colors: array of colors in desired color space, shape (n_colors, 3)
    '''
    if cs == 'RGB':
        return colors
    if cs == 'LAB':
        return sc.rgb2lab(colors[None])[0]
    if cs == 'LCHab':
        colors = sc.rgb2lab(colors[None])
        return sc.lab2lch(colors)[0]
    if cs == 'LCHuv':
        return np.array([convert_color(sRGBColor(*c), LCHuvColor).get_value_tuple() for c in colors])
    if cs == 'XYZ':
        return sc.rgb2xyz(colors[None])[0]
    if cs == 'HSV':
        return sc.rgb2hsv(colors[None])[0]


def cs2rgb(colors, cs):
    '''
    Coverts array of colors from a color space cs to RGB

    # Arguments:
        - colors: array of colorspace colors, shape (n_colors, 3)
        - cs: 'RGB', 'LAB', 'LCHab', 'LCHuv', 'XYZ', 'HSV'

    # Returns:
        - colors: array of colors in RGB, shape (n_colors, 3)
    '''
    if cs == 'RGB':
        return colors
    if cs == 'LAB':
        return sc.lab2rgb(colors[None])[0]
    if cs == 'LCHab':
        colors = sc.lch2lab(colors[None])
        return sc.lab2rgb(colors)[0]
    if cs == 'LCHuv':
        return np.array([convert_color(LCHuvColor(*c), sRGBColor).get_value_tuple() for c in colors])
    if cs == 'XYZ':
        return sc.xyz2rgb(colors[None])[0]
    if cs == 'HSV':
        return sc.hsv2rgb(colors[None])[0]


class Colormap2D(object):
    '''
    Class representing 2D colormap.
    '''

    def __init__(self, color_00, color_10, color_01, color_11, cs='RGB'):
        '''
        Colormap2D constructor.

        # Arguments:
            - color_00: color for value [0,0] in the data space
            - color_10: color for value [1,0] in the data space
            - color_01: color for value [0,1] in the data space
            - color_11: color for value [1,1] in the data space
            - cs: {'RGB', 'LAB', 'LCHab', 'LCHuv', 'XYZ', 'HSV'}, string
                representing color space. Default is 'RGB'.
        '''
        anchor_colors = [color_00, color_10, color_01, color_11]
        self._anchor_colors = np.array([matplotlib.colors.to_rgb(c) for c in anchor_colors])
        self._anchor_colors = rgb2cs(self._anchor_colors, cs)
        self._color_space = cs

    def __call__(self, X):
        '''
        Maps data in X to color space.

        # Arguments:
            - X: array of shape (..., 2). Values must be in range [0,1]

        # Returns:
            - colors: array of shape (..., 3) with color values (floats in
                range [0,1])
        '''
        orig_shape = X.shape
        X = X.reshape(-1,2)
        coefficients = get_coefficients(X)
        colors = (coefficients @ self._anchor_colors)
        colors = cs2rgb(colors, self._color_space)
        colors = colors.reshape(*orig_shape[:-1],3)
        return colors


def generate_2d_cmap(anchor_colors, cs='RGB', steps=100):
    '''
    Takes a list of colors to put into corners. Rest is interpolated.
    anchor_colors: colors for [0,0], [1,0], [0,1], [1,1]
    '''
    cmap = Colormap2D(*anchor_colors, cs)

    x = np.linspace(0,1,steps)
    xx,yy = np.meshgrid(x,x)
    coords = np.stack([xx,yy], axis=-1)
    return cmap(coords)


def plot_cmap(cmap, ax=None):
    '''
    Visualizes a 2D colormap in a given axes.
    '''
    if ax is None:
        ax = plt.gca()

    x = np.linspace(0,1,100)
    xx,yy = np.meshgrid(x,x)
    coords = np.stack([xx,yy], axis=-1)
    preview = cmap(coords)
    ax.imshow(preview)
