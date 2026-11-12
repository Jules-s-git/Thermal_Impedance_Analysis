from __future__ import annotations
from cmath import tau
import subprocess
import numpy as np
from scipy.signal import savgol_filter
from scipy.optimize import minimize, least_squares
from scipy.interpolate import interp1d, PchipInterpolator
from numba import njit, prange
from joblib import Parallel, delayed

"""Cumulative and differential structure functions."""
from .cauer import foster_to_cauer


def cumulative_structure_function(R_cauer, C_cauer):
    """
    Compute the cumulative structure function from a Cauer RC network.

        RΣ(n) = sum_{k=1..n} R_k
        CΣ(n) = sum_{k=1..n} C_k

    Parameters
    ----------
    R_cauer : array_like
        Thermal resistances of the Cauer network [K/W]
    C_cauer : array_like
        Thermal capacitances of the Cauer network [J/K]

    Returns
    -------
    R_cum : ndarray
        Cumulative thermal resistance RΣ [K/W]
    C_cum : ndarray
        Cumulative thermal capacitance CΣ [J/K]
                
    References:
    [4]
    """
    R = np.asarray(R_cauer, dtype=float)
    C = np.asarray(C_cauer, dtype=float)

    R_cum = np.cumsum(R)
    C_cum = np.cumsum(C)

    return R_cum, C_cum

def differential_structure_function(R_cum, C_cum):
    """
    Compute the differential structure function.

        k(RΣ) = dCΣ / dRΣ

    The derivative is piecewise constant between two cumulative
    resistance points, which is why a step representation must be used.

    Parameters
    ----------
    R_cum : ndarray
        Cumulative thermal resistance RΣ [K/W]
    C_cum : ndarray
        Cumulative thermal capacitance CΣ [J/K]

    Returns
    -------
    Rdiff : ndarray
        Resistance axis for differential structure function [K/W]
    dC_dR : ndarray
        Differential structure function dCΣ/dRΣ [JW/K²]
            
    References:
    [4]
    """
    epsilon = 1e-12
    dC_dR = np.diff(C_cum) / (np.diff(R_cum) + epsilon)

    # Differential structure function referenced to cumulative RΣ
    Rdiff = 0.5 * (R_cum[:-1] + R_cum[1:])

    mask = dC_dR > 0

    Rdiff_filtered = Rdiff[mask]
    dC_dR_filtered = dC_dR[mask]

    return Rdiff_filtered, dC_dR_filtered

def structure_function_from_spectrum(R, z):

    R = np.asarray(R, float)
    z = np.asarray(z, float)

    # Midpoints
    Rmid = 0.5 * (R[:-1] + R[1:])
    zmid = 0.5 * (z[:-1] + z[1:])

    # Time constants
    tau_mid = np.exp(zmid)  # make sure z is ln(tau)

    # Cumulative capacitance
    dC = Rmid * tau_mid
    Rmid, dC = foster_to_cauer(Rmid, dC)
    C_cum = np.cumsum(dC)

    # Cumulative resistance
    R_cum = np.cumsum(Rmid)  # simple sum of R increments

    # Differential structure function
    dC_dR = tau_mid
    return R_cum, C_cum, dC_dR, zmid
