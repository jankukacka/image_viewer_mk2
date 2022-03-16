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
from time import time
from queue import Empty
from functools import reduce
from skimage.transform import resize
from multiprocessing import Process, Queue
from matplotlib.colors import PowerNorm

try:
    from .filters.pipeline import Pipeline
except ImportError:
    from filters.pipeline import Pipeline


def render(rendering_queue, rendered_queue, use_gpu, debug, drop_tasks=True):
    '''
    Code for the rendering process
    '''
    image_local = None
    image_local_changed = False
    pipelines = {}
    cache = {}
    while True:
        ## Flush old tasks, work only on the last one
        ## NOTE: This is only reliable with a single consumer thread
        task = rendering_queue.get()
        if task is not None and 'image' in task:
            image_local = task['image']
            image_local_changed = True

        if drop_tasks:
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

        time_render = 0
        time_validation = 0
        time_coloring = 0
        t0 = time()
        try:
            processed_images = []
            response_images = []
            if image_local_changed:
                pipelines = {}
                colors = {}
                image_local_changed = False


            for channel_index, channel_property in enumerate(task['channel_properties']):
                ## Ignore hidden channels
                if not channel_property['visible']:
                    bkg = np.zeros((128,256,4), dtype=np.uint8)
                    bkg[::32] = bkg[-1] = bkg[:,::32] = bkg[:,-1] = 0x66
                    response_images.append(bkg)
                    continue

                image = image_local[...,channel_index]
                t1 = time()
                if (channel_index not in pipelines
                    or pipelines[channel_index].update(channel_property['pipeline'])
                    or channel_property['color'] != colors[channel_index]):

                    if channel_index not in pipelines:
                        pipelines[channel_index] = Pipeline.deserialize(channel_property['pipeline'])
                    t2 = time()
                    mn,mx = image.min(), image.max()
                    image = (image-mn)/(mx-mn)
                    output_image = pipelines[channel_index](image)

                    colors[channel_index] = channel_property['color']
                    cmap = hp.plots.cmap((0,'#444444'),(1/256, 'k'), (1,channel_property['color']))
                    response_image = render_response(image, output_image, cmap)
                    t3 = time()
                    output_image = hp.plots.cmap('k', channel_property['color'])(output_image)
                    t4 = time()
                    cache[channel_index] = output_image, response_image
                else:
                    t2 = time()
                    output_image, response_image = cache[channel_index]
                    t4 = t3 = time()

                time_render += t3-t2
                time_validation += t2-t1
                time_coloring += t4-t3
                processed_images.append(output_image)
                response_images.append(response_image)

            ## Render
            t5 = time()
            ## NOTE: reduce is faster here than stacking the list of arrays and
            ##       calling np.sum on them
            render = reduce(np.add, processed_images)
            render = np.minimum(render, 1) * 255
            render = Image.fromarray(render.astype(np.uint8))
            t6 = time()
            # if debug:
            #     print(f'Pipeline validation: {time_validation:.3f} Rendering: {time_render:.3f} Coloring: {time_coloring:.3f} Sum: {t6-t5:.3f} Total: {t6-t0:.3f}')
            rendered_queue.put((render, response_images))
        except Exception as e:
            if debug:
                track = traceback.format_exc()
                print('Error in Rendering Thread:')
                print(track)

    ## Signal finish of the rendered queue before quitting - it needs to be emptied
    rendered_queue.put(None)


def render_response(input_image, output_image, cmap):
    response = np.empty((128,256,4))
    response[:] = cmap(np.linspace(0,1,response.shape[0]))[:,None]
    hist = np.histogram2d(output_image.ravel(), input_image.ravel(),
                          bins=(np.linspace(0,1,64),np.linspace(0,1,128)))[0]
    with np.seterr(all='ignore'):
        hist = np.log(hist)
    hist = np.nan_to_num(0.5 + 0.5*(hist / hist.max()), neginf=0)
    response[...,-1] = resize(hist, response.shape[:2], preserve_range=True)
    response = (255*response).astype(np.uint8)[::-1]
    bkg = np.zeros_like(response)
    bkg[::32] = bkg[-1] = bkg[:,::32] = bkg[:,-1] = 0x66
    mask = response[:,:,-1] == 0
    response[mask] = bkg[mask]
    return response
