from __future__ import annotations
from cmath import tau
import subprocess
import numpy as np
from scipy.signal import savgol_filter
from scipy.optimize import minimize, least_squares
from scipy.interpolate import interp1d, PchipInterpolator
from numba import njit, prange
from joblib import Parallel, delayed

"""Utilities: log-time derivatives, filtering, peak/pole detection."""

# np.trapz no longer exists in NumPy 2.5; np.trapezoid (NumPy >= 2.0) is the
# same function. Same result with every NumPy version.
trapz = getattr(np, "trapezoid", None) or np.trapz


def safe_log_time(time, eps=1e-12):
    """
    Return log(time) with numerical safety for t <= 0
    """
    t = np.asarray(time, float)
    t = np.maximum(t, eps)
    return np.log(t)

def dZ_dln_t(time, Z, window_length=5, polyorder=2):
    """
    Compute dZ / dln(t) safely, with optional Savitzky-Golay smoothing.

    Parameters
    ----------
    time : array_like
        Time array
    Z : array_like
        Z values
    window_length : int, optional
        Length of the filter window (must be odd and >= polyorder+2)
    polyorder : int, optional
        Polynomial order for Savitzky-Golay filter

    Returns
    -------
    z : array_like
        ln(time)
    deriv : array_like
        Smoothed dZ / dln(t), same length as Z
    """
    z = safe_log_time(time)
    dZ = np.diff(Z)
    dz = np.diff(z)
    deriv = dZ / dz

    # apply the Savitzky-Golay filter
    if len(deriv) >= window_length:
        deriv_smooth = savgol_filter(deriv, window_length=window_length, polyorder=polyorder)
    else:
        deriv_smooth = deriv  # not enough points to filter

    return z, np.concatenate(([0.0], deriv_smooth))

def filter_cumulative_min_resistance(R_cum, C_cum, Rmin):
    """
    Remove cumulative structure points where RΣ < Rmin.
    
    Parameters
    ----------
    R_cum : ndarray
        Cumulative thermal resistance
    C_cum : ndarray
        Cumulative thermal capacitance
    Rmin : float
        Minimum resistance threshold (e.g., smallest physical pole)
        
    Returns
    -------
    Rcum_f : ndarray
    Ccum_f : ndarray
    """
    R_cum = np.asarray(R_cum)
    C_cum = np.asarray(C_cum)

    mask = R_cum >= Rmin

    return R_cum[mask], C_cum[mask]

def pad(array, N):
    """
    Pad an array to length N by repeating the last value if necessary.
    Useful for aligning output arrays to a fixed length for export or display.
    """
    array = np.asarray(array)
    if len(array) >= N:
        return array[:N]
    else:
        # Fill with the last element to reach N
        return np.concatenate([array, np.full(N - len(array), array[-1])])

def detect_min_max(R, time, Z_meas, zero_threshold=1e-24):
    """
    Detect minima and maxima, compute Rth and tau,
    and adjust Rth to minimize absolute deviations from Z_meas.
    """
    R = np.asarray(R).ravel()
    time = np.asarray(time).ravel()
    Z_meas = np.asarray(Z_meas).ravel()
    n = len(R)

    # --- start/end indices ---
    start_ind = np.argmax(R >= zero_threshold)
    end_ind = len(R) - 1 - np.argmax(R[::-1] >= zero_threshold)

    # --- detect maxima/minima ---
    R_safe = np.maximum(R, np.finfo(float).tiny)
    logR = np.log(R_safe)
    dlogR = np.diff(logR)

    minima = [start_ind]
    maxima = []

    for i in range(1, n-1):
        if dlogR[i-1] > 0 and dlogR[i] <= 0:
            maxima.append(i)
        elif R[i-1] > R[i] and R[i] < R[i+1]:
            minima.append(i)
    minima.append(end_ind)

    minima = sorted(set(minima))
    maxima = sorted(set(maxima))

    # Ensure minima exist at beginning and end
    if maxima and maxima[0] < minima[0]:
        minima.insert(0, start_ind)
    if maxima and maxima[-1] > minima[-1]:
        minima.append(end_ind)

    z = np.log(np.maximum(time, np.finfo(float).tiny))
    Rth = np.empty(len(maxima))
    tau = np.empty(len(maxima))
    minima_arr = np.array(minima)

    # Integration of Rth
    for idx, imax in enumerate(maxima):
        left_candidates = minima_arr[minima_arr < imax]
        right_candidates = minima_arr[minima_arr > imax]
        i_min_left = left_candidates.max() if left_candidates.size > 0 else start_ind
        i_min_right = right_candidates.min() if right_candidates.size > 0 else end_ind
        Rth[idx] = trapz(R[i_min_left:i_min_right+1], z[i_min_left:i_min_right+1])
        z_peak = refine_peak(z, R, imax)
        tau[idx] = np.exp(z_peak)

    # --- normalize sum to match Z_meas[-1] ---
    rth_sum = Rth.sum()
    if rth_sum > 0 and np.isfinite(rth_sum):
        Rth *= Z_meas[-1] / rth_sum
    else:
        Rth = np.zeros_like(Rth)  # fallback

    # --- optimization to minimize absolute error ---
    def recon_error(Rth_try):
        Z_recon = np.zeros_like(Z_meas)
        for Ri, ti in zip(Rth_try, tau):
            Z_recon += Ri * (1 - np.exp(-time / ti))
        # total absolute error over all values
        return np.sum(np.abs(Z_recon - Z_meas))

    bounds = [(1e-12, None)] * len(Rth)
    res = minimize(recon_error, Rth, bounds=bounds, method='L-BFGS-B')
    if res.success:
        Rth = res.x
    else:
        # simple fallback
        Rth *= Z_meas[-1] / Rth.sum()

    return Rth, tau

def filter_poles_min_resistance(Rth, tau, Rmin=1e-6):
    """
    Remove poles (Rth, tau) whose resistance is below a physical threshold.

    Parameters
    ----------
    Rth : ndarray
        Pole resistances
    tau : ndarray
        Pole time constants (same length as Rth)
    Rmin : float, optional
        Minimum resistance threshold (poles with Rth < Rmin are discarded).
        Default is 1e-6.

    Returns
    -------
    Rth_f : ndarray
        Filtered resistances
    tau_f : ndarray
        Filtered time constants
    """
    Rth = np.asarray(Rth, float)
    tau = np.asarray(tau, float)

    mask = Rth >= Rmin

    return Rth[mask], tau[mask]

def cauer_structure_function_max_test(Rth, C):
    """
    Filter Cauer network arrays to keep only strictly positive resistance and capacitance values.
    This helps remove non-physical or zero entries from the network.
    """
    R_cauer = np.asarray(Rth)
    C_cauer = np.asarray(C)

    # Keep only strictly positive sections
    mask = (R_cauer > 0) & (C_cauer > 0)

    R_cauer = R_cauer[mask]
    C_cauer = C_cauer[mask]

    return R_cauer, C_cauer

def refine_peak(z, R, i):
    """
    Refine the location of a peak in an array using quadratic interpolation.
    Returns the estimated peak position in z for index i in R.
    """
    if i <= 0 or i >= len(R)-1:
        return z[i]

    x = z[i-1:i+2]
    y = R[i-1:i+2]

    coeffs = np.polyfit(x, y, 2)
    a, b, c = coeffs

    if a == 0:
        return z[i]

    z_peak = -b / (2*a)
    return z_peak
