# ------------------------------------------------------------------------------
#  File: limiter.py
#  Author: Jan Kukacka
#  Date: 3/2019
# ------------------------------------------------------------------------------
#  Widget for scaler with limits and step size
#  Code from https://stackoverflow.com/a/54318377/2042751
# ------------------------------------------------------------------------------


import tkinter as tk
import tkinter.ttk as ttk

class Limiter(ttk.Scale):
    """ ttk.Scale sublass that limits the precision of values. """

    def __init__(self, *args, **kwargs):
        self.resolution = kwargs.pop('resolution', 1)  # Remove non-std kwarg.
        self.chain = kwargs.pop('command', lambda *a: None)  # Save if present.
        super(Limiter, self).__init__(*args, command=self._value_changed, **kwargs)

    def _value_changed(self, newvalue):
        # newvalue = round(float(newvalue), self.precision)
        newvalue = float(newvalue) - self.cget('from')
        newvalue = self.resolution*(newvalue // self.resolution) + self.cget('from')
        winfo_toplevel = self.winfo_toplevel()
        if not isinstance(winfo_toplevel, tk.Tk):
            winfo_toplevel = winfo_toplevel.master
        winfo_toplevel.globalsetvar(self.cget('variable'), (newvalue))
        self.chain(newvalue)  # Call user specified function.
