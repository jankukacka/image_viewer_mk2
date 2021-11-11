import sys
import argparse

try:
    from importlib import metadata
except ImportError: # for Python<3.8
    import importlib_metadata as metadata
__version__ = metadata.version('image-viewer-mk2')

# argument parsing
parser = argparse.ArgumentParser(description='Image Viewer MKII: Spectral image viewer')
parser.add_argument('-i', '--input', type=str, help='Filename of the image to open', default=argparse.SUPPRESS)
parser.add_argument('-c', '--config', type=str, help='Filename of the config file to import', default=argparse.SUPPRESS)

parser.add_argument('-d', '--debug', help='Print errors to console.', action='store_true', default=argparse.SUPPRESS)
parser.add_argument('-g', '--gpu', help='Use GPU rendering (default)', action='store_true', default=argparse.SUPPRESS)
parser.add_argument('-ng', '--no_gpu', help='Use CPU rendering', action='store_true', default=argparse.SUPPRESS)


def main(args=None):
    from . import app
    kwargs = vars(parser.parse_args(sys.argv[1:]))
    kwargs2 = {}

    if 'no_gpu' in kwargs:
        kwargs2['gpu'] = not kwargs['no_gpu']
    if 'gpu' in kwargs:
        kwargs2['gpu'] = kwargs['gpu']
    if 'input' in kwargs:
        kwargs2['file'] = kwargs['input']
    if 'config' in kwargs:
        kwargs2['config_filename'] = kwargs['config']
    if 'debug' in kwargs:
        kwargs2['debug'] = kwargs['debug']

    print(f'Image Viewer MKII (v{__version__}) Jan Kukacka, 2021.')
    app.start(**kwargs2)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception:
        sys.exit(1)
