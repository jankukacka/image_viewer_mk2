# ------------------------------------------------------------------------------
#  File: app.py
#  Author: Jan Kukacka
#  Date: 3/2021
# ------------------------------------------------------------------------------
#  A simple tool for displaying of images
#  run from parent directory as: python -m image_viewer_mk2.app
# ------------------------------------------------------------------------------


from . import view as view_
from . import model as model_
from . import presenter as presenter_

def main(file=None, image=None, **kwargs):
    '''
    Starts the app and opens optionally given files or uses given images.
    If combining files and images, make sure that they occupy different indices
    in the given lists, and use None to pad overlapping positions, e.g.:
    files = [filename1, None]
    images = [None, image2]

    # Returns
    - rendered image as numpy array (height, width, RGBA)
    '''

    gpu = True
    if 'gpu' in kwargs:
        gpu = kwargs['gpu']

    view = view_.View()
    with model_.Model(use_gpu=gpu) as model:
        presenter = presenter_.Presenter(view, model)
        # if file is None and image is None:
        #     model.filename = 'image_viewer_mk2/test_data/Study_90_Scan_4_Frame_21_NMF.nrrd'

        if file is not None:
            model.filename = file

        if image is not None:
            model.update_image(image)


        presenter.mainloop()
        result = np.array(model.render)
    return result

if __name__ == '__main__':
    import sys
    files = sys.argv[1:]
    if len(files) == 0:
        files = None
    main(files)
