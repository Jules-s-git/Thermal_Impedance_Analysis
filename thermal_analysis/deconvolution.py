from __future__ import annotations
from cmath import tau
import subprocess
import numpy as np
from scipy.signal import savgol_filter
from scipy.optimize import minimize, least_squares
from scipy.interpolate import interp1d, PchipInterpolator
from numba import njit, prange
from joblib import Parallel, delayed

"""Richardson–Lucy deconvolution in the log-time domain."""


def my_deconv(deriv_temp, z, M=200, eps=1e-12):
    """
    Perform Richardson–Lucy deconvolution in the logarithmic time domain.

    Parameters:
        deriv_temp : dZth / dln(t)
        z          : ln(time)
        M          : number of RL iterations
        eps        : numerical regularization threshold

    Returns:
        R : recovered thermal spectrum R(z)

    References:
        [3]
    """
    deriv_temp = np.asarray(deriv_temp, float)
    z = np.asarray(z, float)
    n = len(z)

    R = np.ones(n) * 1e-6  # positive initialization

    zdiff = z[:, None] - z[None, :]
    zdiff = np.clip(zdiff, -50, 50)
    exp_zdiff = np.exp(zdiff)
    A = np.exp(np.clip(zdiff - exp_zdiff, -50, 50))
    A /= np.sum(A, axis=0, keepdims=True)
    A = np.nan_to_num(A)

    A_sub = A[1:, :]
    A_sub_j = A_sub[:, 1:]
    dt_sub = deriv_temp[1:]

    for _ in range(M):
        denom = np.maximum(A_sub_j @ R[1:], eps)
        for j in range(1, n):
            update = np.sum(A_sub[:, j] * dt_sub / denom)
            if np.isfinite(update):
                R[j] *= update
            R[j] = np.clip(R[j], 0, 1e6)

    return R

@njit
def my_deconv_numba(deriv_temp, z, M, eps=1e-12):
    """
    Numba version of my_deconv for performance.
    """
    n = len(z)
    R = np.ones(n) * 1e-6  # positive initialization

    # Build matrix A
    A = np.empty((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            zdiff = z[i] - z[j]
            zdiff = min(max(zdiff, -50.0), 50.0)
            exp_zdiff = np.exp(zdiff)
            val = np.exp(min(max(zdiff - exp_zdiff, -50.0), 50.0))
            A[i, j] = val

    # Normalize columns
    for j in range(n):
        col_sum = 0.0
        for i in range(n):
            col_sum += A[i, j]
        if col_sum != 0.0:
            for i in range(n):
                A[i, j] /= col_sum

    # RL iterations
    for _ in range(M):
        denom = np.empty(n-1, dtype=np.float64)
        for j in range(1, n):
            s = 0.0
            for k in range(1, n):
                s += A[k, j] * R[k]
            denom[j-1] = max(s, eps)

        for j in range(1, n):
            s = 0.0
            for k in range(1, n):
                s += A[k, j] * deriv_temp[k] / denom[j-1]
            R[j] *= s

    return R
