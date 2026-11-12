# -*- coding: utf-8 -*-
"""Complete analysis of one thermal impedance curve.

One function, ``analyse``, runs the whole chain used by the window and by
the command line, so both give the same Foster network:

    derivative -> choice of M -> scan of tau -> joint least squares
    -> Cauer network -> structure functions

The two front ends only differ in how they compute the structure functions,
chosen with ``structure``:

* ``"pyrth"`` (window): PyRth on a Foster curve rebuilt on 500 points;
* ``"cauer"`` (command line): cumulative sums of the Cauer network.

Every setting comes from ``thermal_analysis.config``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from . import config
from .cauer import foster_to_cauer
from .deconvolution import my_deconv
from .foster import generate_foster_signal, reconstruct_foster
from .optimization import (optimize_M_range_parallel, optimize_tau_sequential_parallel,
                           refine_foster_least_squares)
from .structure_functions import cumulative_structure_function, differential_structure_function
from .utils import cauer_structure_function_max_test, dZ_dln_t, filter_cumulative_min_resistance

Progress = Optional[Callable[[str], None]]


@dataclass
class AnalysisResult:
    """Everything the window and the command line display or save."""
    time: np.ndarray
    Z_meas: np.ndarray
    n_branches: int
    z: np.ndarray = None              # ln(t)
    dZ_dz: np.ndarray = None          # dZth / dln(t) of the data
    M_opt: int = None                 # chosen number of Richardson-Lucy iterations
    Rth_deconv: np.ndarray = None     # Foster network found by the deconvolution (before
    tau_deconv: np.ndarray = None     #   the scan of tau and the joint least squares)
    Rth_foster: np.ndarray = None     # K/W
    tau_foster: np.ndarray = None     # s
    C_foster: np.ndarray = None       # J/K
    Z_foster: np.ndarray = None       # Zth rebuilt from the Foster network
    z_rec: np.ndarray = None          # derivative and spectrum of Z_foster
    dZ_rec: np.ndarray = None
    R_spec: np.ndarray = None         # spectrum of the data
    R_rec: np.ndarray = None          # spectrum of the Foster curve
    Rth_cauer: np.ndarray = None      # K/W
    C_cauer: np.ndarray = None        # J/K
    Rth_cum: np.ndarray = None        # cumulative structure function
    C_cum: np.ndarray = None
    Rth_diff: np.ndarray = None       # differential structure function
    dC_dRth: np.ndarray = None
    notes: list = field(default_factory=list)


def clean_array(arr, max_val=None):
    """Replace NaN with 0 and +-inf with +-max_val, then clip to +-max_val."""
    max_val = config.CLEAN_MAX_VALUE if max_val is None else max_val
    arr = np.nan_to_num(arr, nan=0.0, posinf=max_val, neginf=-max_val)
    return np.clip(arr, -max_val, max_val)


def _say(progress: Progress, text: str):
    if progress is not None:
        progress(text)


def identify_foster(time, Z_meas, n_branches, progress: Progress = None, result=None):
    """Derivative, choice of M and scan of the time constants.

    Returns (Rth, tau, result): the Foster network before the joint least
    squares, and the AnalysisResult with z, dZ_dz and M_opt filled in.
    """
    res = result or AnalysisResult(np.asarray(time, float), np.asarray(Z_meas, float), int(n_branches))
    t, Z = res.time, res.Z_meas

    res.z, res.dZ_dz = dZ_dln_t(t, Z)

    _say(progress, "Optimizing M values (parallel)...")
    res.M_opt, R, tau, res.Z_foster, _ = optimize_M_range_parallel(
        res.dZ_dz, res.z, t, Z, M_min=config.M_MIN, M_max=config.M_MAX,
        step=config.M_STEP, n_jobs=config.N_JOBS)
    res.Rth_deconv, res.tau_deconv = np.asarray(R, float), np.asarray(tau, float)

    _say(progress, "Optimizing tau values (parallel)...")
    tau, _ = optimize_tau_sequential_parallel(
        t, Z, R, tau, min_factor=config.TAU_FACTOR_MIN, max_factor=config.TAU_FACTOR_MAX,
        step_factor=config.TAU_FACTOR_STEP, n_jobs=config.N_JOBS)
    return R, tau, res


def analyse(time, Z_meas, n_branches=None, structure="pyrth", spectra=True,
            progress: Progress = None) -> AnalysisResult:
    """Run the whole analysis on one curve.

    Parameters
    ----------
    time, Z_meas : array_like
        Time (s) and thermal impedance (K/W), with time > 0, increasing.
    n_branches : int, optional
        Maximum number of Foster branches (config.DEFAULT_MAX_BRANCHES).
    structure : "pyrth" or "cauer"
        How to compute the structure functions: "pyrth" as the window,
        "cauer" as the command line.
    spectra : bool
        Also compute the derivative and the spectrum of the Foster curve, and
        the spectrum of the data (shown by the window).
    progress : callable, optional
        Called with a short status text before each long step.
    """
    if n_branches is None:
        n_branches = config.DEFAULT_MAX_BRANCHES
    res = AnalysisResult(np.asarray(time, float), np.asarray(Z_meas, float), int(n_branches))
    t, Z = res.time, res.Z_meas

    if structure == "pyrth":
        _say(progress, "Running PyRth evaluation...")
    R, tau, res = identify_foster(t, Z, n_branches, progress, res)

    if structure == "pyrth" and config.GUI_RUN_UNUSED_PYRTH_LASSO:  # switch C3
        import PyRth
        evaluation = PyRth.Evaluation()
        evaluation.optimization_module(dict(config.PYRTH_LASSO, data=np.column_stack([t, Z])))

    _say(progress, "Refining Foster fit (global least-squares)...")
    R, tau = refine_foster_least_squares(t, Z, R, tau, n_branches)
    res.Rth_foster, res.tau_foster = np.asarray(R, float), np.asarray(tau, float)
    res.Z_foster = reconstruct_foster(t, res.Rth_foster, res.tau_foster)
    res.C_foster = res.tau_foster / res.Rth_foster if len(res.Rth_foster) > 0 else np.array([])

    if spectra:
        res.z_rec, res.dZ_rec = dZ_dln_t(t, res.Z_foster)
        res.R_rec = my_deconv(res.dZ_rec, res.z_rec, M=res.M_opt)
        res.R_spec = my_deconv(res.dZ_dz, res.z, M=res.M_opt)

    if structure == "cauer":
        _cauer_structure(res)
    elif structure == "pyrth":
        _pyrth_structure(res)
    else:
        raise ValueError(f"unknown structure method {structure!r}")
    return res


def _cauer_structure(res: AnalysisResult):
    """Command line: Cauer network and structure functions from it."""
    if len(res.Rth_foster) > 0:
        rc, cc = foster_to_cauer(res.Rth_foster, res.C_foster)
    else:
        rc, cc = [], []
    res.Rth_cauer, res.C_cauer = cauer_structure_function_max_test(rc, cc)
    r_cum, c_cum = cumulative_structure_function(res.Rth_cauer, res.C_cauer)
    res.Rth_cum, res.C_cum = filter_cumulative_min_resistance(
        r_cum, c_cum, Rmin=config.CLI_MIN_CUMULATIVE_RESISTANCE)
    res.Rth_diff, res.dC_dRth = differential_structure_function(res.Rth_cum, res.C_cum)


def _pyrth_structure(res: AnalysisResult):
    """Window: structure functions from PyRth on the rebuilt Foster curve."""
    import PyRth

    t_min = res.time[-1] / config.SF_TIME_SPAN
    if config.GUI_STRUCTURE_FROM_FIRST_TIME:  # switch C2: never start after the first point
        t_min = min(res.time[0], t_min)
    rebuilt = generate_foster_signal(res.Rth_foster, res.C_foster, res.time[-1],
                                     config.SF_REBUILT_POINTS, t_min=t_min)
    evaluation = PyRth.Evaluation()
    module = evaluation.standard_module(dict(config.PYRTH_STANDARD, data=rebuilt))
    r_cum, c_cum = module.int_cau_res, module.int_cau_cap

    if config.GUI_CONVERT_TO_CAUER and len(res.Rth_foster) > 0:  # switch C1
        rc, cc = foster_to_cauer(res.Rth_foster, res.C_foster)
    else:
        rc, cc = res.Rth_foster, res.C_foster
    res.Rth_cauer, res.C_cauer = cauer_structure_function_max_test(rc, cc)

    # Points below the smallest Foster resistance are dropped (as in Zth_to_Foster,
    # where the "Cauer" table held the Foster resistances).
    r_pos = res.Rth_foster[res.Rth_foster > 0]
    r_min = np.min(r_pos) if len(r_pos) > 0 else 0
    r_cum, c_cum = filter_cumulative_min_resistance(r_cum, c_cum, r_min)
    r_diff, k = differential_structure_function(r_cum, c_cum)
    res.Rth_cum, res.C_cum = clean_array(r_cum), clean_array(c_cum)
    res.Rth_diff, res.dC_dRth = clean_array(r_diff), clean_array(k)
