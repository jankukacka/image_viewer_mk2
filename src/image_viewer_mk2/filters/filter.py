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
        self.active = True

    def __call__(self, img):
        raise NotImplementedError()

    def serialize(self):
        return {'name': self.name,
                'params': {'active': self.active}}

    @staticmethod
    def deserialize(serialization):
        raise NotImplementedError()

    def _deserialize_parent(self, serialization):
        self.active = serialization['active']
