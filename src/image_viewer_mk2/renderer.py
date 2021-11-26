# ------------------------------------------------------------------------------
#  File: renderer.py
#  Author: Jan Kukacka
#  Date: 11/2021
# ------------------------------------------------------------------------------
#  Image rendering thread code
# ------------------------------------------------------------------------------

import traceback
import numpy as np
import happy as hp
from PIL import Image
from queue import Empty
from multiprocessing import Process, Queue
from matplotlib.colors import PowerNorm


## Cache for storing rendered images
## __CHANNEL_CACHE[channel_index] = (channel_props, (rendered_image, response_image))
__CHANNEL_CACHE = {}

def render_channel(channel_index, channel_property, image, fx):
    '''
    Caching wrapper to render_channel_internal function
    '''
    if channel_index not in __CHANNEL_CACHE:
        __CHANNEL_CACHE[channel_index] = ({}, None)

    if __CHANNEL_CACHE[channel_index][0] == channel_property:
        return __CHANNEL_CACHE[channel_index][1]

    ## Else - render image and save it to the cache
    result = render_channel_internal(channel_property, image, fx)
    __CHANNEL_CACHE[channel_index] = (channel_property, result)
    return result


def render_channel_internal(channel_property, image, fx):
    torch = fx['torch']

    if channel_property['use_local_contrast']:
        local_norm = fx['local_norm']
        image = local_norm(image,
                           channel_property['local_contrast_neighborhood'],
                           channel_property['local_contrast_cut_off'])
    image = (image-image.min())/(image.max() - image.min())
    response_x = np.linspace(0,1,128)
    response_y = response_x

    if torch is not None:
        histogram = torch.histc(image, bins=128, min=0, max=1)
    else:
        histogram = np.histogram(image, bins=np.linspace(0,1,129), density=True)[0]

    if channel_property['use_sigmoid']:
        sigmoid_norm = fx['sigmoid_norm']
        image, (low, high) = sigmoid_norm(image,
                                          channel_property['sigmoid_low'],
                                          channel_property['sigmoid_high'],
                                          channel_property['sigmoid_new_low'],
                                          channel_property['sigmoid_new_high'])

        lower = channel_property['sigmoid_new_low']/100
        upper = channel_property['sigmoid_new_high']/100
        new_low = np.log(1e-8+lower/(1-lower))
        new_high = np.log(upper/(1-upper+1e-8))
        response_y = (new_high-new_low) * (response_x-low)/(high-low+1e-8) + new_low
        response_y = 1/(1+np.exp(-response_y))
        response_y = (response_y-response_y.min()) / response_y.ptp()


    if channel_property['use_gamma']:
        response_y = PowerNorm(channel_property['gamma'])(response_y)
        if torch is not None:
            image = (image-image.min())/(image.max() - image.min())
            image = torch.pow(image, channel_property['gamma'])
        else:
            image = PowerNorm(channel_property['gamma'])(image)

    if torch is not None:
        histogram2 = torch.histc(image, bins=128, min=0, max=1)
    else:
        histogram2 = np.histogram(image, bins=np.linspace(0,1,129), density=True)[0]
    histogram, histogram2 = histogram / histogram[1:].max(), histogram2 / histogram2[1:].max()

    ## Convert GPU image to numpy
    if torch is not None:
        image = image.cpu().numpy()

    image = hp.plots.cmap('k', channel_property['color'])(image)

    # ## Generate response image
    if torch is not None:
        response_image = torch.ones((128,128), device=histogram.device)
        mask = (128*torch.log(1+histogram[:,None])) > torch.arange(128, device=histogram.device)
        response_image[mask.T] = .7

        mask = (128*torch.log(1+histogram2[:,None])) > torch.arange(128, device=histogram2.device)
        response_image[mask.flip(1)] *= .5

        response_image[np.round(127*response_y).astype(int), np.arange(128)] = 0
        response_image = response_image.flip(0)*255
        response_image = response_image.cpu().numpy()
    else:
        response_image = np.ones((128,128))

        mask = (128*np.log(1+histogram[:,None]))>np.arange(128)
        response_image[mask.T] = .7

        mask = (128*np.log(1+histogram2[:,None]))>np.arange(128)
        response_image[mask[:,::-1]] *= .5

        response_image[np.round(127*response_y).astype(int), np.arange(128)] = 0
        response_image = response_image[::-1]*255

    return image, response_image


def render(rendering_queue, rendered_queue, use_gpu, debug):
    '''
    Code for the rendering process
    '''

    torch = None
    if use_gpu:
        try:
            import torch
            import torchvision.transforms.functional as ttf

            use_cuda = torch.cuda.is_available()
            device = torch.device("cuda" if use_cuda else "cpu")
            torch.set_grad_enabled(False)

            def local_norm(img, kernel_size=31, cutoff_percent=80):
                '''
                Performs local normalization of a given image relative to the neighborhood
                of size (kernel_size, kernel_size)  using a global cutoffself.

                # Arguments:
                    - img: tensor with the image of shape (height, width)
                    - kernel_size: size of the averaging kernel or tuple of (kernel_height,
                        kernel_width). Should be odd ints.
                    - cutoff_percentile: int between 0 and 100. Global percentile cut-off,
                        preventing over-amplification of noise.

                # Returns:
                    - norm_img: image of the same size as the input img, with values locally
                        normalized.
                '''
                kernel_size = hp.misc.ensure_list(kernel_size)
                if len(kernel_size) == 1:
                    kernel_size = (kernel_size[0], kernel_size[0])

                norm = ttf.gaussian_blur(img.unsqueeze(0), kernel_size, [k/3 for k in kernel_size]).squeeze(0)
                cutoff = torch.max(norm) * np.power(cutoff_percent/100, 3)
                norm_img = img / torch.maximum(norm, cutoff)
                norm_img = torch.nan_to_num(norm_img)

                img = (img-torch.min(img))/(torch.max(img)-torch.min(img))
                norm_img = (norm_img-torch.min(norm_img))/(torch.max(norm_img)-torch.min(norm_img))
                return (img+norm_img)/2

            def sigmoid_norm(a, lower=3, upper=97, new_lower=None, new_upper=None):
                '''
                Performs sigmoid normalization of the given image, by scaling the data
                between given percentiles to range [-1;1], which then sigmoid normalizes to
                "nearly 0" and "nearly 1". Values outside given percentile are squeezed to
                the remaining range.

                # Arguments:
                    - a: array of data to be normalized
                    - lower: percentile between 0 and 100, must be lower than `upper`.
                    - upper: percentile between 0 and 100, must be higher than `lower`.
                    - new_lower: percentile between 0 and 100, where lower will be mapped on
                        the sigmoid curve
                    - new_upper: percentile between 0 and 100, where upper will be mapped on
                        the sigmoid curve

                # Returns:
                    - normalized array.
                    - low, high percentile values
                '''
                eps = 1e-8

                ## Default behavior is like sigmoid_norm_v2
                if new_lower is None:
                    new_lower = lower
                if new_upper is None:
                    new_upper = upper

                # low = torch.quantile(a,lower/100)
                # high = torch.quantile(a,upper/100)
                low = lower/100
                high = upper/100

                lower = new_lower/100
                upper = new_upper/100
                new_low = np.log(eps + lower/(1-lower))  # eps to avoid log(0)
                new_high = np.log(upper/(1-upper+eps))   # eps to avoid division by 0
                a = (new_high-new_low) * (a-low)/(high-low+eps) + new_low
                a = 1/(1+torch.exp(-a))
                # return (a-a.min()) / (a.max()-a.min()), (low.cpu().numpy(), high.cpu().numpy())
                return (a-a.min()) / (a.max()-a.min()), (low, high)

            print('Using GPU acceleration with PyTorch backend:')
            print('PyTorch', torch.__version__)
        except ImportError:
            print('PyTorch not found! Fallig back to using CPU rendering.')
            torch = None

    if torch is None:
        print('Using CPU rendering with NumPy backend:')
        print('NumPy', np.__version__)

        def local_norm(img, kernel_size=31, cutoff_percent=80):
            '''
            Performs local normalization of a given image relative to the neighborhood
            of size (kernel_size, kernel_size)  using a global cutoffself.

            # Arguments:
                - img: tensor with the image of shape (channels, height, width)
                - kernel_size: size of the averaging kernel or tuple of (kernel_height,
                    kernel_width). Should be odd ints.
                - cutoff_percentile: int between 0 and 100. Global percentile cut-off,
                    preventing over-amplification of noise.

            # Returns:
                - norm_img: image of the same size as the input img, with values locally
                    normalized.
            '''
            from scipy.ndimage import gaussian_filter
            kernel_size = hp.misc.ensure_list(kernel_size)
            if len(kernel_size) == 1:
                kernel_size = (kernel_size[0], kernel_size[0])

            norm = gaussian_filter(img, [k/3 for k in kernel_size])
            cutoff = np.max(norm) * np.power(cutoff_percent/100, 3)
            norm_img = img / np.maximum(norm, cutoff)
            norm_img = np.nan_to_num(norm_img)

            img = (img-img.min())/img.ptp()
            norm_img = (norm_img-norm_img.min())/norm_img.ptp()

            return (img+norm_img)/2

        def sigmoid_norm(a, lower=3, upper=97, new_lower=None, new_upper=None):
            '''
            Performs sigmoid normalization of the given image, by scaling the data
            between given percentiles to range [-1;1], which then sigmoid normalizes to
            "nearly 0" and "nearly 1". Values outside given percentile are squeezed to
            the remaining range.

            # Arguments:
                - a: array of data to be normalized
                - lower: percentile between 0 and 100, must be lower than `upper`.
                - upper: percentile between 0 and 100, must be higher than `lower`.
                - new_lower: percentile between 0 and 100, where lower will be mapped on
                    the sigmoid curve
                - new_upper: percentile between 0 and 100, where upper will be mapped on
                    the sigmoid curve

            # Returns:
                - normalized array.
                - low, high percentile values
            '''
            eps = 1e-8

            ## Default behavior is like sigmoid_norm_v2
            if new_lower is None:
                new_lower = lower
            if new_upper is None:
                new_upper = upper

            low = lower/100
            high = upper/100

            lower = new_lower/100
            upper = new_upper/100
            new_low = np.log(eps + lower/(1-lower))  # eps to avoid log(0)
            new_high = np.log(upper/(1-upper+eps))   # eps to avoid division by 0
            a = (new_high-new_low) * (a-low)/(high-low+eps) + new_low
            a = 1/(1+np.exp(-a))
            return (a-a.min()) / (a.max()-a.min()), (low, high)

    fx = {'local_norm': local_norm, 'sigmoid_norm': sigmoid_norm, 'torch': torch}

    image_tensor = None
    image_local = None
    image_local_changed = False

    while True:
        ## Flush old tasks, work only on the last one
        ## NOTE: This is only reliable with a single consumer thread
        task = rendering_queue.get()
        if task is not None and 'image' in task:
            image_local = task['image']
            image_local_changed = True

        try:
            while True:
                task = rendering_queue.get(False)
                # task = rendering_queue.get(True, .05)
                if task is not None and 'image' in task:
                    image_local = task['image']
                    image_local_changed = True
                # print('Dropping a task')
        except Empty:
            pass

        ## Termination signal
        if task is None:
            # print('Exiting rendering thread')
            break

        try:
            processed_images = []
            response_images = []
            if image_local_changed:
                if torch is not None:
                    image_tensor = torch.tensor(image_local).to(device)
                global __CHANNEL_CACHE
                __CHANNEL_CACHE = {}
                image_local_changed = False


            for channel_index, channel_property in enumerate(task['channel_properties']):
                ## Ignore channel name
                del channel_property['name']

                ## Ignore hidden channels
                if not channel_property['visible']:
                    response_images.append(None)
                    continue

                if torch is not None:
                    image = image_tensor[..., channel_index]
                else:
                    image = image_local[...,channel_index]

                image, response_image = render_channel(channel_index, channel_property, image, fx)
                processed_images.append(image)
                response_images.append(response_image)

            ## Render
            render = np.stack(processed_images, axis=-1)
            render = np.sum(render, axis=(-1))
            render = np.minimum(render, 1) * 255
            render = Image.fromarray(render.astype(np.uint8))
            rendered_queue.put((render, response_images))
        except Exception as e:
            if debug:
                track = traceback.format_exc()
                print('Error in Rendering Thread:')
                print(track)

    ## Signal finish of the rendered queue before quitting - it needs to be emptied
    rendered_queue.put(None)
