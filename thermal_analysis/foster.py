from __future__ import annotations
from cmath import tau
import subprocess
import numpy as np
from scipy.signal import savgol_filter
from scipy.optimize import minimize, least_squares
from scipy.interpolate import interp1d, PchipInterpolator
from numba import njit, prange
from joblib import Parallel, delayed

"""Foster network: spectrum <-> RC branches, Zth reconstruction."""
from .utils import safe_log_time


def spectrum_to_foster(R, time, n_branches=8):
    """
    Convert RL spectrum to a Foster RC network via logarithmic integration.

    Returns:
        Rth : Foster resistances
        tau : Foster time constants

    References:
    [2]
    """
    z = safe_log_time(time)

    dln = np.diff(z)
    R_mid = 0.5 * (R[:-1] + R[1:])
    dR = R_mid * dln
    tau_mid = np.sqrt(time[:-1] * time[1:])

    bins = np.linspace(z.min(), z.max(), n_branches + 1)

    Rth = np.zeros(n_branches)
    tau = np.zeros(n_branches)

    z_tau = np.log(tau_mid)

    for i in range(n_branches):
        mask = (z_tau >= bins[i]) & (z_tau < bins[i+1])
        if not np.any(mask):
            continue

        Rth[i] = np.sum(dR[mask])
        tau[i] = np.exp(np.sum(np.log(tau_mid[mask]) * dR[mask]) / Rth[i])

    return Rth, tau

def reconstruct_foster(time, Rth, tau):
    """
    Vectorized: Reconstruct Zth(t) from a Foster RC network.
    """
    time = np.asarray(time, float)
    Rth = np.asarray(Rth, float)
    tau = np.asarray(tau, float)
    # Outer product, then sum over poles
    Z = (Rth[:, None] * (1 - np.exp(-time[None, :] / tau[:, None]))).sum(axis=0)
    return Z

@njit
def reconstruct_foster_numba(time, Rth, tau):
    """
    Numba version of reconstruct_foster
    """
    time = np.asarray(time, float)
    Z = np.zeros_like(time)

    for Ri, ti in zip(Rth, tau):
        Z += Ri * (1 - np.exp(-time / ti))

    return Z

def generate_foster_signal(R, C, t_max, n_points, t_min=None):
    """
    Generate a thermal impedance signal:
        Z(t) = Σ R_i * (1 - exp(-t/tau_i))

    Parameters
    ----------
    R : array_like
        Foster resistances
    tau : array_like
        Foster time constants
    t_max : float
        Maximum time (seconds)
    n_points : int
        Number of time points
    t_min : float, optional
        Minimum time (default = t_max / 1e6)

    Returns
    -------
    data : ndarray (n_points x 2)
        Column 0 : time
        Column 1 : Z(t)

    Also prints a copy-paste ready block:
        time    Zth
    """

    R = np.asarray(R, dtype=float)
    C = np.asarray(C, dtype=float)

    if t_min is None:
        t_min = t_max / 1e6  # wide logarithmic span

    # Logarithmic time spacing (recommended for thermal systems)
    time = np.logspace(np.log10(t_min), np.log10(t_max), n_points)

    Z = np.zeros_like(time)
    for Ri, Ci in zip(R, C):
        Z += Ri * (1 - np.exp(-time / (Ci*Ri)))

    data = np.column_stack((time, Z))

    # Format for paste (tab-separated, no header)
    text_output = "\n".join(
        f"{time:.10e}\t{z:.10e}" for time, z in data
    )

    return data

def foster_network(self):
    """Convert the time-constant spectrum into parallel Foster branches.

    Removes padded zeros, optionally oversamples the spectrum, culls tiny
    entries, and creates the resistance/capacitance arrays that represent
    each Foster branch.  These values are the shared starting point for the
    MPFR-based rational reconstruction and every Foster→Cauer converter.
    """

    factor = int(self.timespec_interpolate_factor)

    if factor > 1:
        f = np.interp.InterpolatedUnivariateSpline(self.log_time_pad, self.time_spec)
        int_log_time = np.linspace(
            self.log_time_pad.min(),
            self.log_time_pad.max(),
            len(self.log_time_pad) * factor,
        )
        int_time_spec = f(self.log_time_pad)
    else:
        int_log_time = self.log_time_pad.copy()
        int_time_spec = self.time_spec.copy()

    where = np.where(int_time_spec >= 1e-10)
    self.crop_time_spec = int_time_spec[where]
    self.crop_log_time = int_log_time[where]

    if self.crop_time_spec.size == 0:
        raise ValueError("Time constant spectrum is empty after filtering.")

    self.therm_resist_fost = self.crop_time_spec
    self.therm_capa_fost = np.exp(self.crop_log_time) / self.therm_resist_fost
