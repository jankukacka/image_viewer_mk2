# ------------------------------------------------------------------------------
#  File: model.py
#  Author: Jan Kukacka
#  Date: 3/2021
# ------------------------------------------------------------------------------
#  Application data model component
# ------------------------------------------------------------------------------

import numpy as np
import traceback
import happy as hp
from matplotlib.colors import PowerNorm
from multiprocessing import Process, Queue
from queue import Empty

from PIL import ImageTk, Image

from .ObservableCollections.observablelist import ObservableList
from .ObservableCollections.observabledict import ObservableDict
from .ObservableCollections.observable import Observable
from .ObservableCollections.event import Event

class Model(Observable):
    '''
    Data model object
    '''

    def __init__(self, use_gpu=True):
        Observable.__init__(self)

        ## Setup image rendering process
        self.rendering_queue = Queue()
        self.rendered_queue = Queue()
        self.rendering_process = Process(target=render, args=(self.rendering_queue, self.rendered_queue, use_gpu))

        ## Setup IO process
        self.io_task_queue = Queue()
        self.io_response_queue = Queue()
        self.io_process = Process(target=reader, args=(self.io_task_queue, self.io_response_queue))
        self.n_io_pending = 0

        self._filename = None
        self._image = None
        self._color_space = 'RGB'
        self._render = None
        self.suspend_render = False

        # self.histograms = None
        # self.responses = None
        self.response_images = None

        self.channel_props = ObservableList()
        self.channel_props.attach(lambda e, self=self: self.raiseEvent('propertyChanged', propertyName='channel_props', child=e))


        imoptions = {
            'use_unsharp_mask': True,
            'unsharp_mask_radius': 0.5,
            'unsharp_mask_amount': 1.0,
            'wavelength': 10,
            'wavelength_median': 5
        }
        self.imoptions = ObservableDict(imoptions)
        self.imoptions.attach(lambda x, self=self: self.raiseEvent('propertyChanged', propertyName='imoptions'))
        self.imoptions.attach(self.update_render)

        self.special_options = {
            ## Allows to selectively switch off unsharp mask for channel 2
            'no_sharpening_channel_2': False
        }

    def __enter__(self):
        self.rendering_process.start()
        self.io_process.start()
        return self

    def __exit__(self, type, value, traceback):
        ## Send termination signals
        self.rendering_queue.put(None)
        self.io_task_queue.put(None)

        ## Empty the result queues
        render = 1
        while render is not None:
            render = self.rendered_queue.get()

        io_response = 1
        while io_response is not None:
            io_response = self.io_response_queue.get()

        ## Join processes
        self.rendering_process.join()
        self.io_process.join()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, val):
        if val is not self._filename:
            self._filename = val
            self.raiseEvent('propertyChanged', propertyName='filename')
            self.load_image()
            # image =
            # self.update_image(image)

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, val):
        if val is not self._image:
            self._image = val
            self.raiseEvent('propertyChanged', propertyName='image')
            e = Event('propertyChanged', self)
            e.propertyName = 'image'
            self.update_render(e)

    @property
    def color_space(self):
        return self._color_space

    @color_space.setter
    def color_space(self, val):
        if val is not self._color_space:
            self._color_space = val
            self.raiseEvent('propertyChanged', propertyName='color_space')
            self.update_cmap()

    @property
    def render(self):
        return self._render

    @render.setter
    def render(self, val):
        self._render = val
        self.raiseEvent('propertyChanged', propertyName='render')

    def load_image(self, event=None):
        task = {'type': 'load_image', 'filename':self.filename}
        self.io_task_queue.put(task)
        self.n_io_pending += 1
        self.raiseEvent('ioTask')

    def update_image(self, image):
        '''
        Used to update the image and reload channels
        '''
        self.suspend_render = True
        self.image = image
        self.update_channels()
        self.suspend_render = False
        e = Event('propertyChanged', self)
        e.propertyName = 'image'
        self.update_render(e)

    def update_channels(self):
        ## Clear old channel props
        while len(self.channel_props) > 0:
            del self.channel_props[0]

        n_channels = self.image.shape[2]

        for channel in range(n_channels):
            channel_property = {}
            channel_property['use_local_contrast'] = True
            channel_property['local_contrast_neighborhood'] = 31
            channel_property['local_contrast_cut_off'] = 80
            channel_property['use_gamma'] = True
            channel_property['gamma'] = 1
            channel_property['use_sigmoid'] = True
            channel_property['sigmoid_low'] = 0
            channel_property['sigmoid_high'] = 100
            channel_property['sigmoid_new_low'] = 49
            channel_property['sigmoid_new_high'] = 51
            channel_property['color'] = '#ffffff'
            channel_property['visible'] = True

            channel_property = ObservableDict(channel_property)
            channel_property.attach(lambda x, self=self: self.raiseEvent('propertyChanged', propertyName='channel_props'))
            channel_property.attach(self.update_render)
            self.channel_props.append(channel_property)


    def check_for_render(self):
        try:
            # render, self.histograms, self.responses = self.rendered_queue.get_nowait()
            render, self.response_images = self.rendered_queue.get_nowait()
            self.render = render
        except Empty as e:
            pass

    def check_for_io(self):
        try:
            response = self.io_response_queue.get_nowait()
            self.n_io_pending -= 1
            if response['type'] == 'load_image':
                self.update_image(response['image'])
        except Empty as e:
            pass


    def update_render(self, event=None):
        ## Check we have all images
        if self.image is None:
            return
        ## Check render is not suspended
        if self.suspend_render:
            return

        render_task = {}
        render_task['channel_properties'] = [dict(channel_property) for channel_property in self.channel_props]
        render_task['imoptions'] = dict(self.imoptions)
        render_task['special_options'] = self.special_options

        ## If image has changed, pass it to the rendering thread too
        if event is not None and event.action == 'propertyChanged' and event.propertyName == 'image':
            render_task['image'] = self.image

        self.rendering_queue.put(render_task)

    def save(self):
        model_dict = {}
        # model_dict['colors'] = list(self.colors)
        # model_dict['color_space'] = self.color_space
        # model_dict['imoptions'] = dict(self.imoptions)
        model_dict['channel_props'] = [dict(cp) for cp in self.channel_props]
        # model_dict['special_options'] = dict(self.special_options)
        return model_dict

    def load(self, model_dict):
        ## Suspend rendering while loading
        self.suspend_render = True

        # for i, color in enumerate(model_dict['colors']):
        #     self.colors[i] = color
        # self.color_space = model_dict['color_space']
        # for key, value in model_dict['imoptions'].items():
        #     self.imoptions[key] = value
        for i, channel_property in enumerate(model_dict['channel_props']):
            if i >= len(self.channel_props):
                break
            for key, value in channel_property.items():
                self.channel_props[i][key] = value
        # if 'special_options' in model_dict:
        #     self.special_options = model_dict['special_options']

        self.suspend_render = False
        self.update_render()

    def transpose_image(self):
        self.image = self.image.transpose(1,0,2)


def render(rendering_queue, rendered_queue, use_gpu):
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
                task = rendering_queue.get(True, .25)
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
            if image_local_changed and torch is not None:
                image_tensor = torch.tensor(image_local).to(device)
                image_local_changed = False


            for channel_index, channel_property in enumerate(task['channel_properties']):
                ## Ignore hidden channels
                if not channel_property['visible']:
                    response_images.append(None)
                    continue

                if torch is not None:
                    image = image_tensor[..., channel_index]
                else:
                    image = image_local[...,channel_index]
                if channel_property['use_local_contrast']:
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
                processed_images.append(image)

                # ## Generate response image
                if torch is not None:
                    response_image = torch.ones((128,128), device=device)
                    mask = (128*torch.log(1+histogram[:,None])) > torch.arange(128, device=device)
                    response_image[mask.T] = .7

                    mask = (128*torch.log(1+histogram2[:,None])) > torch.arange(128, device=device)
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

                response_images.append(response_image)
            ## Render
            render = np.stack(processed_images, axis=-1)
            # print('Render shape', render.shape, render.dtype)
            # render = task['colormap'](render) * 255
            render = np.sum(render, axis=(-1))
            render = np.minimum(render, 1) * 255
            render = Image.fromarray(render.astype(np.uint8))
            # rendered_queue.put((render, histograms, responses))
            rendered_queue.put((render, response_images))
        except Exception as e:
            track = traceback.format_exc()
            print('Error in Rendering Thread:')
            print(track)
    ## Signal finish of the rendered queue before quitting - it needs to be emptied
    rendered_queue.put(None)


def reader(input_queue, output_queue):
    while True:
        task = input_queue.get()

        ## Termination signal
        if task is None:
            # print('Exiting rendering thread')
            break

        try:
            response = {'type': task['type']}
            if task['type'] == 'load_image':
                filename = task['filename']
                response['image'] = load_image_internal(filename)
                # except Exception:
                #     print('Error loading image')
                #     response['image'] = None

            output_queue.put(response)

        except Exception as e:
            track = traceback.format_exc()
            print('Error in IO Thread:')
            print(track)
            response['exception'] = True
            output_queue.put(response)



    ## Signal finish of the rendered queue before quitting - it needs to be emptied
    output_queue.put(None)


def load_image_internal(filename):
    image = hp.io.load(filename)

    ## Handle MAT files:
    try:
        keys = [k for k in image.keys() if 'rec' in k]
        if len(keys) == 1:
            image = image[key]
        else:
            print('Could not load image (ambiguous keys)')
    except Exception:
        pass

    if image.ndim == 2:
        image = image[...,None]

    return image
