# ------------------------------------------------------------------------------
#  File: observable.py
#  Author: Remi Emonet
#  Date: 8/2019
#  Source: https://github.com/twitwi/vuejs-python/tree/master/vuejspython/observablecollections
#  License: MIT
# ------------------------------------------------------------------------------

import types
from .event import Event

class Observable:
	def __init__(self):
		self.observers = set()

	def attach(self, observer):
		if (observer not in self.observers):
			self.observers.add(observer)

	def detach(self, observer):
		if (observer in self.observers):
			self.observers.remove(observer)

	def raiseEvent(self, name, **kwargs):
		event = Event(name, self)

		for key, value in kwargs.items():
			setattr(event, key, value)

		for eventObserver in self.observers:
			eventObserver(event)
