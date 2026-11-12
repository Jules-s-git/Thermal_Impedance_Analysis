from __future__ import annotations
from cmath import tau
import subprocess
import numpy as np
from scipy.signal import savgol_filter
from scipy.optimize import minimize, least_squares
from scipy.interpolate import interp1d, PchipInterpolator
from numba import njit, prange
from joblib import Parallel, delayed

"""Foster model fitting (M, tau, least squares)."""
from .deconvolution import my_deconv
from .foster import reconstruct_foster
from .utils import detect_min_max, filter_poles_min_resistance, trapz
from . import config


def spectrum_to_foster_max_detection_test(R, time, 

                                          zero_threshold=1e-12,
                                          points_per_decade=6):
    """
    Convert a thermal resistance spectrum to Foster network parameters by binning the spectrum in log-time intervals.
    Integrates the spectrum within each bin to estimate Foster resistances and time constants.
    Useful for extracting a compact Foster model from a measured or computed spectrum.
    """

    R = np.asarray(R)
    time = np.asarray(time)

    # Work in log-time
    logt = np.log10(time)

    # Create uniform log grid
    t_min, t_max = logt[0], logt[-1]
    n_bins = int((t_max - t_min) * points_per_decade)

    log_bins = np.linspace(t_min, t_max, n_bins + 1)
    tau_centers = 10 ** ((log_bins[:-1] + log_bins[1:]) / 2)

    Rth = []
    C = []

    for i in range(n_bins):

        mask = (logt >= log_bins[i]) & (logt < log_bins[i+1])

        if not np.any(mask):
            continue

        # integrate spectrum inside bin
        dR = trapz(R[mask], time[mask])

        if dR <= zero_threshold:
            continue

        tau = tau_centers[i]

        Rth.append(dR)
        C.append(tau / dR)

    return np.array(Rth), np.array(C)

def spectrum_to_foster_max_detection_test_log2(
        R,
        z,
        points_per_decade=10,
        energy_threshold=1e-12,
        merge_ratio=0.05
    ):
    # 1) regular grid
    z_min, z_max = z[0], z[-1]
    decades = (z_max - z_min) / np.log(10)
    n_points = max(int(decades * points_per_decade), 2)
    z_reg = np.linspace(z_min, z_max, n_points)
    
    # interpolation of R on the regular grid
    R_interp = np.interp(z_reg, z, R)
    
    Rth = []
    Cth = []
    
    # 2) trapezoidal integration interval by interval
    for i in range(len(z_reg)-1):
        dz = z_reg[i+1] - z_reg[i]
        dR = 0.5 * (R_interp[i] + R_interp[i+1]) * dz
        
        if dR <= 0:
            continue
        
        # exact tau over the interval
        tau = (np.exp(z_reg[i+1]) - np.exp(z_reg[i])) / np.log(np.exp(z_reg[i+1])/np.exp(z_reg[i]))
        
        Rth.append(dR)
        Cth.append(tau / dR)
    
    Rth = np.array(Rth)
    Cth = np.array(Cth)
    
    if len(Rth) == 0:
        return Rth, Cth
    
    # 3) remove negligible poles
    total_R = np.sum(Rth)
    mask = Rth > energy_threshold * total_R
    Rth = Rth[mask]
    Cth = Cth[mask]
    
    # 4) light merging of small neighbouring poles
    Rth_new = []
    Cth_new = []
    
    i = 0
    while i < len(Rth):
        current_R = Rth[i]
        current_tau = Cth[i] * Rth[i]
        
        j = i + 1
        while j < len(Rth) and Rth[j] < merge_ratio * np.max(Rth):
            current_R += Rth[j]
            current_tau += Cth[j] * Rth[j]
            j += 1
        
        Rth_new.append(current_R)
        Cth_new.append(current_tau / current_R)
        
        i = j
    
    Rth_new = np.array(Rth_new)
    Cth_new = np.array(Cth_new)
    
    # 5) global adjustment to keep the integral exactly
    factor = np.sum(R_interp * np.diff(np.concatenate(([0], z_reg)))) / np.sum(Rth_new)
    Rth_new *= factor
    Cth_new /= factor  # so that Rth*Cth stays the same
    
    return Rth_new, Cth_new

def optimize_M_range(R_dZ, z, time, Z_meas, root=None, status_label=None, M_min=1, M_max=300,  step=2):
    """
    Find the M value (number of RL iterations) that minimizes
    the total absolute deviation between reconstructed and measured Zth.

    Parameters:
        R_dZ, z, time, Z_meas : data arrays
        root : Tk root, used for GUI updates (optional)
        status_label : ttk.Label, used to display progress (optional)
        M_min, M_max : range of M to test
    """
    best_M = M_min
    min_error = np.inf
    best_Rth = best_tau = best_Zf = None

    for M in range(M_min, M_max + 1, step):
        # GUI update every 5 iterations to reduce slowdown
        if status_label is not None and root is not None and (M - M_min) % (5*step) == 0:
            status_label.config(text=f"Testing M = {M} / {M_max}")
            root.update()

        R = my_deconv(R_dZ, z, M)
        Rth, tau = detect_min_max(R, time, Z_meas)
        Zf = reconstruct_foster(time, Rth, tau)
        error = np.sum(np.abs(Zf - Z_meas))

        if error < min_error:
            min_error = error
            best_M = M
            best_Rth = Rth
            best_tau = tau
            best_Zf = Zf

    if status_label is not None and root is not None:
        status_label.config(text=f"Optimization complete. Best M = {best_M}, error = {min_error:.6g}")
        root.update()

    return best_M, best_Rth, best_tau, best_Zf, min_error

def optimize_tau_sequential(time, Z_meas, Rth, tau,
                            min_factor=0.5,
                            max_factor=2.0,
                            step_factor=0.1):
    """
    Sequentially optimize each tau by scanning a multiplicative range
    and minimizing total absolute reconstruction error.

    Parameters
    ----------
    time : ndarray
    Z_meas : ndarray
    Rth : ndarray
    tau : ndarray
    min_factor : float (default 0.5)
    max_factor : float (default 2.0)
    step_factor : float (default 0.1)

    Returns
    -------
    tau_opt : ndarray
    best_error : float
    """

    tau_opt = np.array(tau, dtype=float)
    Rth = np.array(Rth, dtype=float)

    # Initial error
    Z_current = reconstruct_foster(time, Rth, tau_opt)
    best_error = np.sum(np.abs(Z_current - Z_meas))

    factors = np.arange(min_factor, max_factor + step_factor, step_factor)

    for i in range(len(tau_opt)):
        tau_i = tau_opt[i]
        # Vectorized scan for this tau
        tau_candidates = tau_i * factors
        # Broadcast Rth and tau for all candidates
        errors = np.array([np.sum(np.abs(reconstruct_foster(time, Rth, np.concatenate([tau_opt[:i], [t], tau_opt[i+1:]])) - Z_meas))
                   for t in tau_candidates])
        best_idx = np.argmin(errors)
        tau_opt[i] = tau_candidates[best_idx]
        best_error = errors[best_idx]

    return tau_opt, best_error

def optimize_M_range_parallel(R_dZ, z, time, Z_meas,
                              M_min=1, M_max=300, step=2, n_jobs=-1):
    # ensure arrays are float64
    R_dZ = np.asarray(R_dZ, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    time = np.asarray(time, dtype=np.float64)
    Z_meas = np.asarray(Z_meas, dtype=np.float64)

    def process_M(M):
        R = my_deconv(R_dZ, z, M)
        Rth, tau = detect_min_max(R, time, Z_meas)
        Rth = np.asarray(Rth, dtype=np.float64)
        tau = np.asarray(tau, dtype=np.float64)
        Zf = reconstruct_foster(time, Rth, tau)
        error = np.sum(np.abs(Zf - Z_meas))
        return M, Rth, tau, Zf, error

    # --- Two-stage search: coarse, then fine ---
    coarse_step = max(10, step)
    coarse_Ms = list(range(M_min, M_max + 1, coarse_step))
    coarse_results = Parallel(n_jobs=n_jobs, backend="threading")(delayed(process_M)(M) for M in coarse_Ms)
    best_coarse = min(coarse_results, key=lambda x: x[4])
    best_M_coarse = best_coarse[0]
    # Fine search around best coarse M
    fine_M_min = max(M_min, best_M_coarse - coarse_step)
    fine_M_max = min(M_max, best_M_coarse + coarse_step)
    fine_Ms = list(range(fine_M_min, fine_M_max + 1, step))
    fine_results = Parallel(n_jobs=n_jobs, backend="threading")(delayed(process_M)(M) for M in fine_Ms)
    best = min(fine_results, key=lambda x: x[4])
    return best

def optimize_tau_sequential_parallel(time, Z_meas, Rth, tau,
                                     min_factor=0.5, max_factor=2.0, step_factor=0.1, n_jobs=-1):
    tau_opt = np.array(tau, dtype=float)
    Rth = np.array(Rth, dtype=float)

    Z_current = reconstruct_foster(time, Rth, tau_opt)
    best_error = np.sum(np.abs(Z_current - Z_meas))

    factors = np.arange(min_factor, max_factor + step_factor, step_factor)

    for i in range(len(tau_opt)):
        tau_i = tau_opt[i]
        tau_candidates = tau_i * factors
        # Vectorized: try all tau_candidates at once
        tau_matrix = np.tile(tau_opt, (len(tau_candidates), 1))
        tau_matrix[:, i] = tau_candidates
        # Each row is a tau vector
        Zf_matrix = np.array([reconstruct_foster(time, Rth, tau_vec) for tau_vec in tau_matrix])
        errors = np.sum(np.abs(Zf_matrix - Z_meas), axis=1)
        best_idx = np.argmin(errors)
        tau_opt[i] = tau_candidates[best_idx]
        best_error = errors[best_idx]

    return tau_opt, best_error

def refine_foster_least_squares(time, Z_meas, Rth_init, tau_init, max_poles, max_error = 0.002):#0.005
    """
    Jointly optimize Rth and tau for Foster model to best fit Z_meas (L2 norm).
    If the fit is too far off, add a pole at the location of maximum error and re-optimize.
    Minimum number of poles is number of poles detected in R_spectrum 
    """
    time = np.asarray(time, float)
    Z_meas = np.asarray(Z_meas, float)
    Rth_init = np.asarray(Rth_init, float)
    tau_init = np.asarray(tau_init, float)
    n = len(Rth_init)
    if n > max_poles:
        if config.FILTER_SMALL_POLES:  # switch D1
            return filter_poles_min_resistance(Rth_init, tau_init, Rmin=config.MIN_POLE_RESISTANCE)
        return Rth_init, tau_init
    
    def model(params):
        Rth = params[:n]
        tau = params[n:]
        return (Rth[:, None] * (1 - np.exp(-time[None, :] / tau[:, None]))).sum(axis=0)

    def residuals(params):
        return model(params) - Z_meas

    # Bounds: Rth > 0, tau > 0
    lb = [1e-12] * n * 2
    ub = [np.inf] * n * 2
    x0 = np.concatenate([Rth_init, tau_init])
    result = least_squares(residuals, x0, bounds=(lb, ub), method='trf', ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=2000)
    Rth_opt = result.x[:n]
    tau_opt = result.x[n:]
    cost = result.cost

    # Check if error is too high (relative RMSE)
    Z_fit = model(np.concatenate([Rth_opt, tau_opt]))
    rel_rmse = np.sqrt(np.mean((Z_fit - Z_meas) ** 2)) / (np.max(Z_meas) - np.min(Z_meas) + 1e-12)

    poles_added = 0
    while rel_rmse > max_error and n < max_poles:
        # Find where the error is largest
        abs_err = np.abs(Z_fit - Z_meas)
        idx_max = np.argmax(abs_err)
        # Add a new pole at this time constant
        # Current maximum value
        R_max = np.max(Rth_opt)

        # Estimate of the new Rth
        Rth_new = abs_err[idx_max] / (1 - np.exp(-1))  # crude estimate

        # Criterion: if Rth_new is too small compared to R_max, this pole is ignored
        if Rth_new * 1e5 < R_max:
            break  # stop the loop, no new pole
        tau_new = time[idx_max]
        # Estimate Rth for new pole: proportional to error at that point
        Rth_new = abs_err[idx_max] / (1 - np.exp(-1))  # crude estimate
        # Add to the arrays
        Rth_opt = np.append(Rth_opt, Rth_new)
        tau_opt = np.append(tau_opt, tau_new)
        n += 1
        # Re-optimize
        lb = [1e-12] * n * 2
        ub = [np.inf] * n * 2
        x0 = np.concatenate([Rth_opt, tau_opt])
        def model_n(params):
            Rth = params[:n]
            tau = params[n:]
            return (Rth[:, None] * (1 - np.exp(-time[None, :] / tau[:, None]))).sum(axis=0)
        def residuals_n(params):
            return model_n(params) - Z_meas
        result = least_squares(residuals_n, x0, bounds=(lb, ub), method='trf', ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=2000)
        Rth_opt = result.x[:n]
        tau_opt = result.x[n:]
        Z_fit = model_n(np.concatenate([Rth_opt, tau_opt]))
        rel_rmse = np.sqrt(np.mean((Z_fit - Z_meas) ** 2)) / (np.max(Z_meas) - np.min(Z_meas) + 1e-12)
        poles_added += 1

    # Filter out non-physical poles (resistance too low), switch D1
    if config.FILTER_SMALL_POLES:
        Rth_opt, tau_opt = filter_poles_min_resistance(Rth_opt, tau_opt, Rmin=config.MIN_POLE_RESISTANCE)

    return Rth_opt, tau_opt
