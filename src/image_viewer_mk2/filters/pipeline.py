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

    def __call__(self, img):
        for filter in self.filters:
            img = filter(img)
        return img

    def serialize(self):
        return {'filters': [filter.serialize() for filter in self.filters]}

    @staticmethod
    def call(serialization, img):
        for filter in serialization['filters']:
            params = filter['params']
            if params['active']:
                T_filter = filter_factory.get_filter_by_name(filter['name'])
                img = T_filter.call(img, **params)
        return img

    @staticmethod
    def deserialize(serialization):
        filters = []
        for filter in serialization['filters']:
            T_filter = filter_factory.get_filter_by_name(filter['name'])
            filter = T_filter.deserialize(filter['params'])
            filters.append(filter)
        return Pipeline(filters)


    def update(self, serialization):
        '''
        Update filters in the pipeline and invalidates cache of existing filters
        if a change is detected in an earlier stage

        # Arguments:
            - serialization: Dict with serialized pipeline.

        # Returns:
            - change_detected: Bool. True if Pipeline was updated, False if
                serialization was matching the current pipeline.
        '''
        change_detected = False
        for i, filter in enumerate(serialization['filters']):
            if i >= len(self.filters):
                T_filter = filter_factory.get_filter_by_name(filter['name'])
                new_filter = T_filter.deserialize(filter['params'])
                self.filters.append(new_filter)
                change_detected = True
            if self.filters[i].serialize() != filter:
                T_filter = filter_factory.get_filter_by_name(filter['name'])
                new_filter = T_filter.deserialize(filter['params'])
                self.filters[i] = new_filter
                change_detected = True
            if change_detected:
                self.filters[i].cache = None
        if len(self.filters) > len(serialization['filters']):
            self.filters = self.filters[:len(serialization['filters'])]
            change_detected = True

        return change_detected
