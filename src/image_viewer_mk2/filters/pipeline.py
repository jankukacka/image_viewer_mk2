# ------------------------------------------------------------------------------
#  File: pipeline.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Filtering pipeline
# ------------------------------------------------------------------------------


try:
    from . import filter_factory
except ImportError:
    from filters import filter_factory

class Pipeline(object):
    '''
    Pipeline contains a sequence of filters to pass an image through
    '''

    def __init__(self, filters):
        self.filters = filters
        self.cache = None

    def __call__(self, img):
        if self.cache is None:
            for filter in self.filters:
                img = filter(img)
            self.cache = img
        return self.cache

    def serialize(self):
        return {'filters': [filter.serialize() for filter in self.filters]}

    @staticmethod
    def deserialize(serialization):
        filters = []
        for filter in serialization['filters']:
            T_filter = filter_factory.get_filter_by_name(filter['name'])
            filter = T_filter.deserialize(filter['params'])
            filters.append(filter)
        return Pipeline(filters)
