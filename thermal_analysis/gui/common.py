# -*- coding: utf-8 -*-
"""Imports and helpers shared by the modules of the window.

The step modules import their dependencies with ``from .common import *``,
as the screens of the KiCad/Icepak application do.
"""

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import Image, ImageTk

from .. import config, data_io, ltspice
from ..foster import reconstruct_foster
from ..pipeline import analyse

# Pictures of the Notice tab, found from the package, whatever the current folder
ASSETS = Path(__file__).resolve().parents[1] / "assets"

ORANGE = "#cc5500"   # frame of unprocessed data, edited rows of the Foster table

__all__ = ["os", "tk", "filedialog", "messagebox", "scrolledtext", "ttk", "plt", "np", "pd",
           "FigureCanvasTkAgg", "NavigationToolbar2Tk", "Image", "ImageTk", "config", "data_io", "ltspice",
           "reconstruct_foster", "analyse", "ASSETS", "ORANGE"]
