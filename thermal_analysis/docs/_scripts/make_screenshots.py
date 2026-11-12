"""Regenerate the screenshots of the window used in the documentation.

Usage, from anywhere (needs a display, or xvfb-run, and ImageMagick):

    python thermal_analysis/docs/_scripts/make_screenshots.py
    xvfb-run -s "-screen 0 1800x1000x24" python thermal_analysis/docs/_scripts/make_screenshots.py

Opens the real window, loads input_data/MEAS_IGBT.xlsx without the file
dialog, clicks Process and captures the window after each step. Screenshots
taken on Linux show the Tk default theme; on Windows the window looks
different but has the same controls.
"""

from __future__ import annotations

import os
import subprocess
import time
import tkinter.filedialog as filedialog

from _tool import DOCS, data_dir, load

FIG = DOCS / "figures"
DATA = str(data_dir() / "MEAS_IGBT.xlsx")


def main():
    ta, name = load()
    gui = __import__(f"{name}.gui", fromlist=["ThermalGUI"])
    app = gui.ThermalGUI(run=False)
    app.root.geometry("1800x1000+0+0")

    def shot(file):
        for _ in range(3):
            app.root.update()
            time.sleep(0.3)
        subprocess.run(["import", "-window", "root", str(FIG / file)], check=True)
        print("written", FIG / file)

    def run():
        filedialog.askopenfilename = lambda **kw: DATA
        app._load_file()
        shot("gui_loaded.png")
        app._process_data()
        shot("gui_zth.png")
        for index, file in ((2, "gui_spectrum.png"), (3, "gui_cumulative.png")):
            app.notebook.select(index)
            shot(file)
        os._exit(0)  # leave without waiting for Tk/Matplotlib teardown

    app.root.after(500, run)
    app.root.mainloop()


if __name__ == "__main__":
    main()
