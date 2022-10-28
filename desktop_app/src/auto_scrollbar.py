import tkinter as tk
import ttkbootstrap as ttk


class AutoScrollbar(ttk.Scrollbar):
    """
    A scrollbar that hides itself if it's not needed.
    Works only if you use the grid geometry manager.
    Source: https://www.geeksforgeeks.org/autohiding-scrollbars-using-python-tkinter/

    """

    # Non-static public methods
    def set(self, lo, hi):
        """
        Hides or shows the scrollbar.

        """

        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError("Cannot use pack with this widget")

    def place(self, **kw):
        raise tk.TclError("Cannot use place with this widget")
