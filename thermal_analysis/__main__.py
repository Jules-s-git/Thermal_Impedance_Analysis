# -*- coding: utf-8 -*-
"""Start the analysis from the package.

    python -m thermal_analysis                       opens the window
    python -m thermal_analysis -file input.xlsx      runs the command line
    python -m thermal_analysis.cli -file input.xlsx  same, explicitly

Running this file directly also works (python thermal_analysis/__main__.py,
or "Run Python File" in VS Code): the folder above the package is then added
to the Python path, so that the package can be imported.
"""

import importlib
import os
import sys

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE = __package__ or os.path.basename(PACKAGE_DIR)


def main():
    if not __package__:  # run as a file, not with -m
        sys.path.insert(0, os.path.dirname(PACKAGE_DIR))
    if len(sys.argv) > 1:
        importlib.import_module(f"{PACKAGE}.cli").main()
    else:
        importlib.import_module(f"{PACKAGE}.gui").main()


if __name__ == "__main__":
    main()
