# -*- coding: utf-8 -*-
"""
Package thermal_analysis — thermal impedance analysis (Zth -> Foster/Cauer).

  * deconvolution        : Richardson–Lucy deconvolution in the log-time domain.
  * foster               : Foster network: spectrum <-> RC branches, Zth reconstruction.
  * cauer                : Foster network -> Cauer network conversion.
  * structure_functions  : cumulative and differential structure functions.
  * utils                : utilities: log-time derivatives, filtering, peak/pole detection.
  * optimization         : Foster model fitting (M, tau, least squares).
  * pipeline             : complete analysis of one curve (analyse).
  * data_io              : reading curves, writing results.
  * ltspice              : LTspice model of a network (subcircuits, symbols, test bench).
  * config               : settings, and switches between the behaviours of
                           this package and of the stand-alone Zth_to_Foster tool.
  * cli, gui             : command line and window (not imported here).

Start the tool:

    python -m thermal_analysis                   window
    python -m thermal_analysis -file data.xlsx   command line
"""

from .deconvolution import *  # noqa: F401,F403
from .foster import *  # noqa: F401,F403
from .cauer import *  # noqa: F401,F403
from .structure_functions import *  # noqa: F401,F403
from .utils import *  # noqa: F401,F403
from .optimization import *  # noqa: F401,F403
from . import config  # noqa: F401
from .pipeline import AnalysisResult, analyse  # noqa: F401

__all__ = [
    'AnalysisResult',
    'analyse',
    'config',
    'cauer_structure_function_max_test',
    'cumulative_structure_function',
    'dZ_dln_t',
    'detect_min_max',
    'differential_structure_function',
    'filter_cumulative_min_resistance',
    'filter_poles_min_resistance',
    'foster_network',
    'foster_to_cauer',
    'generate_foster_signal',
    'my_deconv',
    'my_deconv_numba',
    'optimize_M_range',
    'optimize_M_range_parallel',
    'optimize_tau_sequential',
    'optimize_tau_sequential_parallel',
    'pad',
    'reconstruct_foster',
    'reconstruct_foster_numba',
    'refine_foster_least_squares',
    'refine_peak',
    'safe_log_time',
    'spectrum_to_foster',
    'spectrum_to_foster_max_detection_test',
    'spectrum_to_foster_max_detection_test_log2',
    'structure_function_from_spectrum',
]
