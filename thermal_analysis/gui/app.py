# -*- coding: utf-8 -*-
"""ThermalGUI: the window of the thermal impedance analysis.

The window owns the Tk root and the analysis results (as attributes, with
the names of the stand-alone Zth_to_Foster tool). The controls, plots and
results live in three mixin classes that ThermalGUI inherits; a mixin only
adds methods, so one part can change without touching the others.

    step_input.py    InputMixin    data box, Load File, Process, status
    step_plots.py    PlotsMixin    plot tabs and Notice tab
    step_results.py  ResultsMixin  Foster editor, result tables, copy, export
"""

if not __package__:  # run as a file (python thermal_analysis/gui/app.py): start it as a module
    import os as _os, runpy as _runpy, sys as _sys
    _pkg_dir = _os.path.dirname(_os.path.abspath(__file__))
    _pkg_dir = _os.path.dirname(_pkg_dir)
    _sys.path.insert(0, _os.path.dirname(_pkg_dir))
    _runpy.run_module(_os.path.basename(_pkg_dir) + ".gui.app", run_name="__main__")
    raise SystemExit


from .common import *  # noqa: F401,F403
from .step_input import InputMixin
from .step_plots import PlotsMixin
from .step_results import ResultsMixin


class ThermalGUI(InputMixin, PlotsMixin, ResultsMixin):
    """Main window of the Thermal Impedance Analysis tool."""

    def __init__(self, run=True):
        self.root = tk.Tk()
        self.root.title("Thermal Impedance Analysis tool")
        self.file_loaded = False
        self.file_processed = False
        self._build_controls()
        self._build_plots_and_tables()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        if run:
            self.root.mainloop()

    def _on_close(self):
        plt.close("all")
        self.root.destroy()


def main():
    ThermalGUI()


if __name__ == "__main__":
    main()
