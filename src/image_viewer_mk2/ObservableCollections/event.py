# ------------------------------------------------------------------------------
#  File: event.py
#  Author: Remi Emonet
#  Date: 8/2019
#  Source: https://github.com/twitwi/vuejs-python/tree/master/vuejspython/observablecollections
#  License: MIT
# ------------------------------------------------------------------------------

class Event:
	def __init__(self, action, source):
		self._action = action
		self._source = source

	@property
	def action(self):
		return self._action

	@property
	def source(self):
		return self._source
