# ------------------------------------------------------------------------------
#  File: tk_call_wrapper.py
#  Author: Jan Kukacka
#  Date: 11/2021
# ------------------------------------------------------------------------------
#  Call wrapper for custom error handling
#  based on https://stackoverflow.com/a/35390914/2042751
# ------------------------------------------------------------------------------

import tkinter as tk

class CallWrapper:
    def __init__(self, func, subst, widget):
        self.func = func
        self.subst = subst
        self.widget = widget

    def __call__(self, *args):
        try:
            if self.subst:
                args = self.subst(*args)
            return self.func(*args)
        except SystemExit as msg:
            raise SystemExit(msg)

        except tk.TclError as err:
            pass
