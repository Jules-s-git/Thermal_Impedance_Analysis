from __future__ import annotations
from cmath import tau
import subprocess
import numpy as np
from scipy.signal import savgol_filter
from scipy.optimize import minimize, least_squares
from scipy.interpolate import interp1d, PchipInterpolator
from numba import njit, prange
from joblib import Parallel, delayed

"""Foster network -> Cauer network conversion."""


def foster_to_cauer(Rf, Cf):
    """
    Convert a Foster network (Rf, Cf) into its Cauer equivalent (Rs, Cs).
    
    Parameters:
        Rf : list or array
            Resistances of the Foster network
        Cf : list or array
            Capacitances of the Foster network
            
    Returns:
        Cs : list
            Capacitances of the Cauer network
        Rs : list
            Resistances of the Cauer network

    References:
    [1]
    """
    
    # -------------------------------
    # Step 1: Convert Foster to polynomial form
    # Z(s) = sum_k R_k / (1 + R_k C_k s)
    # -------------------------------
    num = np.array([0.0])
    den = np.array([1.0])
    
    for R, C in zip(Rf, Cf):
        # Polynomial for each branch: 1 + R*C*s
        den_k = np.array([1.0, R*C])  # [constant, s]
        num_k = np.array([R])         # [constant only]
        
        # Convolutions to sum branches
        num1 = np.convolve(num, den_k)
        num2 = np.convolve(den, num_k)
        
        # Pad to the same length on the right (low-order coefficients first)
        max_len = max(len(num1), len(num2))
        num1 = np.pad(num1, (0, max_len - len(num1)), 'constant')
        num2 = np.pad(num2, (0, max_len - len(num2)), 'constant')
        
        num = num1 + num2
        den = np.convolve(den, den_k)
    
    # Remove trailing zeros (highest-order coefficients)
    num = np.trim_zeros(num, 'b')
    den = np.trim_zeros(den, 'b')
    
    # -------------------------------
    # Step 2: Extract Cauer network from polynomials
    # -------------------------------
    Cs = []
    Rs = []
    
    while len(num) > 0:
        # Extract a capacitance from the last coefficient (highest power of s)
        C = den[-1] / num[-1]
        Cs.append(float(C))
        
        # Subtract Cs * shifted numerator from denominator
        num_padded = np.pad(num, (1,0), 'constant')
        den = den - C * num_padded
        den = np.delete(den, -1)  # remove highest-order term (extracted)
        
        if len(den) == 0:
            break
        
        # Extract series resistance
        R = num[-1] / den[-1]
        Rs.append(float(R))
        
        # Update numerator
        num = num - R * den
        num = np.delete(num, -1)  # remove last coefficient
    
    return Rs, Cs
