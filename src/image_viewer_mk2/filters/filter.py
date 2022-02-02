# ------------------------------------------------------------------------------
#  File: filter.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Base class for image processing filters
# ------------------------------------------------------------------------------

class Filter(object):
    '''
    Base class for filters.
    '''

    def __init__(self):
        pass

    def __call__(self, img):
        raise NotImplementedError()

    def serialize(self):
        raise NotImplementedError()

    @staticmethod
    def deserialize(serialization):
        raise NotImplementedError()
