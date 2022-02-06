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
from matplotlib.colors import PowerNorm, to_hex
from multiprocessing import Process, Queue
from queue import Empty
from time import time

from PIL import ImageTk, Image

try:
    from .ObservableCollections.observablelist import ObservableList
    from .ObservableCollections.observabledict import ObservableDict
    from .ObservableCollections.observable import Observable
    from .ObservableCollections.event import Event
    from .ObservableCollections.utils import make_observable, make_plain
    from .renderer import render
    from .filters.pipeline import Pipeline
    from .filters.filter_factory import get_filter_by_name
    from .filters.local_norm import LocalNorm
    from .filters.sigmoid_norm import SigmoidNorm
    from .utils import event_handler
except ImportError:
    from ObservableCollections.observablelist import ObservableList
    from ObservableCollections.observabledict import ObservableDict
    from ObservableCollections.observable import Observable
    from ObservableCollections.event import Event
    from ObservableCollections.utils import make_observable, make_plain
    from renderer import render
    from filters.pipeline import Pipeline
    from filters.filter_factory import get_filter_by_name
    from filters.local_norm import LocalNorm
    from filters.sigmoid_norm import SigmoidNorm
    from utils import event_handler

class Model(Observable):
    '''
    Data model object
    '''

    def __init__(self, use_gpu=True, debug=False, drop_tasks=True):
        super().__init__()

        ## Setup image rendering process
        self.rendering_queue = Queue()
        self.rendered_queue = Queue()
        self.rendering_process = Process(target=render, args=(self.rendering_queue, self.rendered_queue, use_gpu, debug, drop_tasks))

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

        self.response_images = None

        self.channel_props = ObservableList()

        @event_handler.requires('event')
        def on_channelprops_changed(event, obj):
            obj.raiseEvent(name='propertyChanged', propertyName='channel_props', child=event)
        self.channel_props.attach(event_handler.ObservableEventHandler(on_channelprops_changed, obj=self))
        self.channel_prop_clipboard = None


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
            if render is not None:
                self.render = render[0]

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

    def add_filter(self, channel_index, filter):
        '''
        Appends a filter to the rendering pipeline of the given channel

        # Arguments:
            - channel_index: int. Index of the channel to append the filter to.
            - filter: Filter object or filter type name to append
        '''
        T_filter = get_filter_by_name(filter)
        if T_filter is not None:
            filter = T_filter()

        filter_dict = make_observable(filter.serialize())
        self.channel_props[channel_index]['pipeline']['filters'].append(filter_dict)
        filter_dict['params'].attach(event_handler.ObservableEventHandler(self.raiseEvent, name='propertyChanged', propertyName='channel_props'))
        filter_dict['params'].attach(event_handler.ObservableEventHandler(self.update_render))

    def remove_filter(self, channel_index, filter_index):
        '''
        Removes n-th filter from the rendering pipeline of the given channel

        # Arguments:
            - channel_index: int. Index of the channel to append the filter to.
            - filter_index: int. Index of the filter to be removed.
        '''
        del self.channel_props[channel_index]['pipeline']['filters'][filter_index]


    def update_channels(self):
        ## Clear old channel props
        while len(self.channel_props) > 0:
            del self.channel_props[0]

        n_channels = self.image.shape[2]

        for channel in range(n_channels):
            channel_property = {}
            channel_property['name'] = f'Channel {channel}'
            channel_property['pipeline'] = make_observable(Pipeline([LocalNorm(80,10), SigmoidNorm(0,100,49,51)]).serialize())
            channel_property['color'] = '#ffffff'
            channel_property['visible'] = True

            channel_property = ObservableDict(channel_property)
            channel_property.attach(event_handler.ObservableEventHandler(self.raiseEvent, name='propertyChanged', propertyName='channel_props'))
            channel_property.attach(event_handler.ObservableEventHandler(self.update_render))
            # channel_property['pipeline'].attach(lambda x, self=self: self.raiseEvent('propertyChanged', propertyName='channel_props'))
            # channel_property['pipeline'].attach(self.update_render)
            # channel_property['pipeline']['filters'].attach(event_handler.ObservableEventHandler(self.raiseEvent, name='propertyChanged', propertyName='channel_props'))
            channel_property['pipeline']['filters'].attach(event_handler.ObservableEventHandler(self.update_render))
            for item in channel_property['pipeline']['filters']:
                # item['params'].attach(event_handler.ObservableEventHandler(self.raiseEvent, name='propertyChanged', propertyName='channel_props'))
                item['params'].attach(event_handler.ObservableEventHandler(self.update_render))
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


    @event_handler.requires('event')
    def update_render(self, event=None):
        ## Check we have all images
        if self.image is None:
            return
        ## Check render is not suspended
        if self.suspend_render:
            return

        render_task = {}
        render_task['channel_properties'] = make_plain(self.channel_props)

        ## If image has changed, pass it to the rendering thread too
        if event is not None and event.action == 'propertyChanged' and event.propertyName == 'image':
            render_task['image'] = self.image

        self.rendering_queue.put(render_task)

    def save(self):
        model_dict = {}
        model_dict['channel_props'] = [dict(cp) for cp in self.channel_props]
        return model_dict

    def load(self, model_dict):
        ## Suspend rendering while loading
        self.suspend_render = True

        for i, channel_property in enumerate(model_dict['channel_props']):
            if i >= len(self.channel_props):
                break
            for key, value in channel_property.items():
                if key in self.channel_props[i]:
                    self.channel_props[i][key] = value
                else:
                    print(f'Config key {key} could not be loaded.')

        self.suspend_render = False
        self.update_render()

    def transpose_image(self):
        self.image = self.image.transpose(1,0,2)

    def autocolor(self):
        for i, channel_prop in enumerate(self.channel_props):
            channel_prop['color'] = str(to_hex(f'C{i%10}'))

    def copy_params(self, channel_index):
        self.channel_prop_clipboard = dict(self.channel_props[channel_index])

    def paste_params(self, channel_index):
        if self.channel_prop_clipboard is None:
            return
        for key, value in self.channel_prop_clipboard.items():
            if key not in ['name', 'color', 'visible']:
                self.channel_props[channel_index][key] = value



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
