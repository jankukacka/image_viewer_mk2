# ------------------------------------------------------------------------------
#  File: utils.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Helping functions for working with observable collections
# ------------------------------------------------------------------------------

try:
    from .observablelist import ObservableList
    from .observabledict import ObservableDict
except ImportError:
    from ObservableCollections.observablelist import ObservableList
    from ObservableCollections.observabledict import ObservableDict


def make_observable(obj):
    if isinstance(obj, list):
        return ObservableList([make_observable(item) for item in obj])
    elif isinstance(obj, dict):
        return ObservableDict({key:make_observable(val) for key,val in obj.items()})
    elif isinstance(obj, set):
        raise NotImplementedError('make_observable does not support sets.')
    else:
        return obj

def make_plain(obj):
    if isinstance(obj, (list,ObservableList)):
        return [make_plain(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(make_plain(item) for item in obj)
    elif isinstance(obj, (dict,ObservableDict)):
        return {key:make_plain(val) for key,val in obj.items()}
    # elif isinstance(obj, ObservableSet):
    #     raise NotImplementedError('make_plain does not support sets.')
    else:
        return obj
