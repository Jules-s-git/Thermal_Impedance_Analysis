# -*- coding: utf-8 -*-
"""Settings and switches of the thermal impedance analysis.

Every number that drives the analysis is here, and every functional
difference between this package and the stand-alone ``Zth_to_Foster`` tool
is a switch. The functions read this module when they run, so a script can
also change a value before calling them::

    from thermal_analysis import config
    config.FILTER_SMALL_POLES = False

Switches marked [D] are differences that already existed between the two
copies of the code. Switches marked [C] are corrections that neither copy
had; they are on by default. Switches marked [N] are new outputs. Set a
[C] or [N] switch to the value given in its comment to get the behaviour of
``Zth_to_Foster`` back.
"""

# ---------------------------------------------------------------------------
# Switches
# ---------------------------------------------------------------------------

# [D1] refine_foster_least_squares removes the Foster poles whose resistance
# is below MIN_POLE_RESISTANCE (K/W), also when it skips the fit because the
# deconvolution gave more poles than the maximum.
#   True  = thermal_analysis package (KiCad/Icepak project, v47)
#   False = stand-alone Zth_to_Foster: tiny poles are kept
FILTER_SMALL_POLES = True
MIN_POLE_RESISTANCE = 1e-6

# [C1] In the window, convert the Foster network into a Cauer network with
# foster_to_cauer, as the command line does.
#   True  = correction (default)
#   False = Zth_to_Foster: the "Cauer" table repeats the Foster network
GUI_CONVERT_TO_CAUER = True

# [C2] In the window, rebuild the Foster curve for the structure functions
# from the first measured time when it is earlier than t_end / 1e6 (the curve
# then covers all the measured poles; it never starts later than before).
#   True  = correction (default): the structure function ends at Rth
#   False = Zth_to_Foster: the poles faster than t_end / 1e6 are lost and the
#           structure function ends below Rth
GUI_STRUCTURE_FROM_FIRST_TIME = True

# [C3] At the start of Process, the window runs a PyRth lasso evaluation
# whose result is never used (about 1.5 s).
#   False = correction (default): skip it; no result changes
#   True  = Zth_to_Foster: run it
GUI_RUN_UNUSED_PYRTH_LASSO = False

# [C4] Unit shown on the differential structure function axis.
#   "W²·s/K²"  = correct unit of dC/dR (default)
#   "J/K²"     = Zth_to_Foster label (wrong)
DIFFERENTIAL_UNIT_LABEL = "W²·s/K²"

# [N1] The command line also writes the LTspice models of the network: for
# the Foster and the Cauer network, a model <NAME>_<KIND>.net, a symbol
# <NAME>_<KIND>.asy and a test bench <NAME>_<KIND>_testbench.net, as
# kicad_icepak does in v47.
#   True  = new output (default)
#   False = Zth_to_Foster: only the nine text files
CLI_WRITE_LTSPICE = True

# [N2] Excel export of all the results, one sheet per table.
#   True  = new output (default): Export All Data proposes an .xlsx file
#           (a .csv file can still be chosen), and the command line also
#           writes <NAME>_results.xlsx
#   False = Zth_to_Foster: Export All Data proposes a .csv file, and the
#           command line writes no workbook
EXCEL_EXPORT = True

# ---------------------------------------------------------------------------
# Settings of the identification (same values in the window and the CLI)
# ---------------------------------------------------------------------------

DEFAULT_MAX_BRANCHES = 10          # maximum number of Foster branches

# Choice of M, the number of Richardson-Lucy iterations
M_MIN, M_MAX, M_STEP = 1, 300, 2   # coarse step is max(10, M_STEP)
N_JOBS = -1                        # threads for the search over M (-1 = all)

# Scan of the time constants
TAU_FACTOR_MIN, TAU_FACTOR_MAX, TAU_FACTOR_STEP = 0.4, 2.0, 0.01

# Structure functions of the command line: points kept
CLI_MIN_CUMULATIVE_RESISTANCE = 1e-6   # K/W

# Structure functions of the window (PyRth)
SF_REBUILT_POINTS = 500            # points of the rebuilt Foster curve
SF_TIME_SPAN = 1e6                 # rebuilt from t_end / SF_TIME_SPAN, or earlier (C2)
PYRTH_STANDARD = {"calc_struc": True, "deconv_mode": "bayesian",
                  "label": "IGBT_measurement"}
PYRTH_LASSO = {"calc_struc": True, "deconv_mode": "lasso", "lasso_alpha": 0.001,
               "theo_time_size": 500, "log_time_size": 100, "label": "IGBT_sparse"}
CLEAN_MAX_VALUE = 1e20             # NaN -> 0, +-inf -> +-CLEAN_MAX_VALUE

# LTspice model (ltspice.py): window button "Export LTspice" and command line
LTSPICE_DEFAULT_NAME = "ZTH"       # model name when the data were pasted
LTSPICE_TESTBENCH_POWER = 1.0      # W, power step of the test bench
LTSPICE_AMBIENT = 25.0             # degC, ambient of the test bench
