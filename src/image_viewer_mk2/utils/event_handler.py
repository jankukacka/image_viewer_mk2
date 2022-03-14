# ------------------------------------------------------------------------------
#  File: event_handler.py
#  Author: Jan Kukacka
#  Date: 2/2022
# ------------------------------------------------------------------------------
#  Classes for event handling and monitoring event flow in the app
# ------------------------------------------------------------------------------

from time import time
from functools import wraps
from operator import attrgetter
from happy.misc import ensure_list

show_events = False
event_depth = 0

class EventHandler:
    '''
    Base class for event handlers
    '''
    def __init__(self, func, name_=None, **kwargs):
        self.func = func
        self.func_kwargs = kwargs
        self.name = name_

    def __call__(self, *args, event_details=None, **kwargs):
        global show_events, event_depth
        if not show_events:
            self.func(*args, **kwargs)
        else:
            event_depth += 1
            try:
                print(f'{"│  "*(event_depth-2)}{"◇" if event_depth==1 else "├─"}', f'Event ({self.name}): handler = {self.func.__name__} (Details: {event_details})')

                t0 = time()
                self.func(*args, **kwargs)
                t1 = time()
                print(f'{"│  "*(event_depth-2)}{"└◈" if event_depth==1 else "├──┘"}', f' [{t1-t0:.5f} s]')
            finally:
                event_depth -= 1



class TkVarEventHandler(EventHandler):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)

    def __call__(self, varname, varindex, action):
        args = []
        if hasattr(self.func, 'requires'):
            if 'varname' in self.func.requires:
                args.append(varname)
            if 'varindex' in self.func.requires:
                args.append(varindex)
            if 'action' in self.func.requires:
                args.append(action)
        super().__call__(event_details=f'trigger var = {varname}', *args, **self.func_kwargs)


class ObservableEventHandler(EventHandler):
    def __init__(self, func, filter_=None, **kwargs):
        '''
        Initializes handler for events from Observable objects

        # Arguments:
            - func: callable that handles the event
            - filter_: (optional) Dict with keys to match event attributes. Values
                can be strings or lists of strings. Events not matching
                the given strings will be ignored.
        '''
        super().__init__(func, **kwargs)
        if filter_ is not None:
            self.filter = {key: ensure_list(val) for key,val in filter_.items()}
        else:
            self.filter = None


    def __call__(self, event):
        if self.filter is not None:
            try:
                for attr, values in self.filter.items():
                    for value in values:
                        if attrgetter(attr)(event) == value:
                            break
                    else:
                        return
            except AttributeError:
                return

        event_details = f'source = {event.source}, action = {event.action}'
        if event.action == 'propertyChanged' and hasattr(event, 'propertyName'):
            event_details += f'[{event.propertyName}]'
        try:
            if 'event' in self.func.requires:
                super().__call__(event, event_details=event_details, **self.func_kwargs)
            else:
                super().__call__(event_details=event_details,**self.func_kwargs)
        except AttributeError:
            super().__call__(event_details=event_details,**self.func_kwargs)


class TkCommandEventHandler(EventHandler):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)

    def __call__(self):
        super().__call__(**self.func_kwargs)

class TkEventHandler(EventHandler):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)

    def __call__(self, event):
        event_details = f'source = {event.widget}, action = {event.type}'
        try:
            if 'event' in self.func.requires:
                super().__call__(event, event_details=event_details, **self.func_kwargs)
            else:
                super().__call__(event_details=event_details, **self.func_kwargs)
        except AttributeError:
            super().__call__(event_details=event_details, **self.func_kwargs)


def requires(argument_name):
    def decorator(func):
        if not hasattr(func, 'requires'):
            func.requires = {}
        func.requires[argument_name] = True
        return func
    return decorator
