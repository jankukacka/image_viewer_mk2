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
        self.cache = None

    def __call__(self, img):
        '''
        Base class call handler. Child classes need to take care of case when
        this returns None.
        '''
        if not self.active:
            return img
        if self.cache is not None:
            return self.cache

    def serialize(self):
        return {'name': self.name,
                'params': {'active': self.active}}

    @staticmethod
    def deserialize(serialization):
        raise NotImplementedError()

    def _deserialize_parent(self, serialization):
        self.active = serialization['active']
