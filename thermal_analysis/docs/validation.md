# Validation

This page compares the results of the tool with known networks, and gives
the fit quality on the measured files of `input_data`. Every number comes
from `docs/_scripts/validate.py`, which runs `pipeline.analyse` with the
default settings of `config.py`. Run it again after you change the code, and
update the tables.

Test conditions: `thermal_analysis` package with its default settings,
NumPy 1.26.4, SciPy 1.17.1, PyRth 1.2.0, Python 3.13, Linux, 2 processors.
Times are wall-clock times of the identification as the command line runs
it, without PyRth and the plots; the window adds a few seconds.

## Four-cell IGBT network (known values)

The `RECONS_IGBT_*PTS.xlsx` files hold the same Foster network sampled with
50 to 500 points, logarithmically spaced from 50 µs to 50 s. The file gives
the reference values in its *Measured* columns:

| Cell | $R_k$ (K/W) | $\tau_k$ (s) |
|---|---|---|
| 1 | 0.007694 | 0.00015 |
| 2 | 0.010756 | 0.02399 |
| 3 | 0.031688 | 0.828796 |
| 4 | 0.033822 | 5.633773 |

`LTSPICE_IGBT.xlsx` is the same network simulated in LTspice: 535 points
from 9 µs to 50 s, spaced by the LTspice time step, not logarithmically.

| File | Points | Cells found | Largest error on $R_k$ | Largest error on $\tau_k$ | Time (s) |
|---|---|---|---|---|---|
| `RECONS_IGBT_50PTS.xlsx` | 50 | 4 | 0.05 % | 0.29 % | 3 |
| `RECONS_IGBT_75PTS.xlsx` | 75 | 4 | 0.05 % | 0.29 % | 5 |
| `RECONS_IGBT_100PTS.xlsx` | 100 | 4 | 0.05 % | 0.29 % | 6 |
| `RECONS_IGBT_200PTS.xlsx` | 200 | 4 | 0.05 % | 0.29 % | 10 |
| `RECONS_IGBT_300PTS.xlsx` | 300 | 4 | 0.05 % | 0.29 % | 15 |
| `RECONS_IGBT_400PTS.xlsx` | 400 | 4 | 0.05 % | 0.29 % | 22 |
| `RECONS_IGBT_500PTS.xlsx` | 500 | 4 | 0.05 % | 0.29 % | 27 |
| `LTSPICE_IGBT.xlsx` | 535 | 4 | 0.03 % | 1.21 % | 141 |
| `LTSPICE_IGBT.xlsx`, resampled to 20 points per decade | 136 | 4 | 0.27 % | 1.48 % | 7 |

What this shows:

- On the `RECONS` files, the tool finds the four cells from 50 points, that
  is 8 points per decade. The remaining 0.05 % and 0.29 % come from the
  reference values, which are rounded ($\tau_1$ = 0.00015 s): the rebuilt
  curve matches the data within $10^{-8}$ of $R_{th}$.
- The computation time grows faster than the number of points. The
  535 points of the LTspice file, spaced linearly at long times, take 141 s.
  Resampled in log time, the same curve takes 7 s and gives the same cells
  within 1.5 % (see
  [Resample a long or linear curve](howto.md#resample-a-long-or-linear-curve)).
- The *Calculated* columns of the `RECONS` files hold results computed
  earlier, probably with an older version of the tool (for example
  $\tau_1$ = 0.000151 s on the 100-point file). The current version is
  closer to the reference.

## LTspice networks with 1, 3 and 5 cells

The `LTSPICE_MOD*_*RC.xlsx` files are Foster networks of 1, 3 and 5 cells
simulated in LTspice, with values in the thousands rather than in K/W.
Open point: the element values of these networks aren't stored
with the files, so only the fit can be checked.

| File | Points | Time span (s) | Cells after deconvolution | Final cells | $\sum R_k$ / last $Z_{th}$ | Relative RMSE | Largest error / last $Z_{th}$ | Time (s) |
|---|---|---|---|---|---|---|---|---|
| `LTSPICE_MOD1_1RC.xlsx` | 36 | 1.9e-06 to 0.001 | 1 | 1 | 1.0001 | 0.09 % | 0.25 % | 2 |
| `LTSPICE_MOD2_3RC.xlsx` | 57 | 2.3e-06 to 1 | 4 | 3 | 1.0018 | 0.15 % | 0.37 % | 5 |
| `LTSPICE_MOD3_5RC.xlsx` | 78 | 2.3e-06 to 3 | 4 | 4 | 1.0005 | 0.07 % | 0.23 % | 4 |

The tool finds the right number of cells for the 1- and 3-cell networks.
For the 5-cell network it finds 4 cells, which fit within 0.07 %: two cells
are probably too close to be told apart with 78 points, and the fit is
already below the 0.2 % that would add a cell (see
[Limits of the method](method.md#limits-of-the-method)).

"Relative RMSE" is the root mean square error divided by the range of
$Z_{th}$, the criterion of the least-squares step.

## Measured thermal impedances

The `MEAS_*.xlsx` files are measured thermal impedances, sampled at about
14 points per decade. Open point: the measurement set-ups aren't recorded
with the files. `C2M0040120` is a SiC MOSFET reference; `TIM` and `WATER`
suggest two cooling conditions of the same device.

| File | Points | Time span (s) | Cells after deconvolution | Final cells | $\sum R_k$ / last $Z_{th}$ | Relative RMSE | Largest error / last $Z_{th}$ | Time (s) |
|---|---|---|---|---|---|---|---|---|
| `MEAS_C2M0040120_TIM.xlsx` | 126 | 1e-06 to 850 | 5 | 5 | 1.0001 | 0.01 % | 0.04 % | 10 |
| `MEAS_C2M0040120_WATER.xlsx` | 112 | 1e-06 to 85 | 3 | 6 | 0.9991 | 0.12 % | 0.24 % | 6 |
| `MEAS_CPW5.xlsx` | 126 | 1e-06 to 850 | 3 | 7 | 0.9993 | 0.17 % | 0.32 % | 6 |
| `MEAS_DIODE.xlsx` | 126 | 1e-06 to 850 | 4 | 5 | 0.9982 | 0.18 % | 0.35 % | 7 |
| `MEAS_IGBT.xlsx` | 126 | 1e-06 to 850 | 6 | 7 | 0.9987 | 0.13 % | 0.26 % | 8 |

Every fit ends below the 0.2 % target. On four of the five files the
least-squares step added 1 to 4 cells to the cells of the deconvolution.

## Foster to Cauer conversion

`foster_to_cauer` was tested on random Foster networks, with time constants
spread uniformly in log scale and resistances from 0.01 to 1.5 K/W. The
impedance $Z(j\omega)$ of the Cauer ladder was compared with that of the
Foster network over six decades of frequency around the time constants.

| Cells | Spread of $\tau$ | Non-positive elements | Largest error on $Z(j\omega)$ / $R_{th}$ |
|---|---|---|---|
| 4 | 1e5 | 0 | 4.5e-16 |
| 10 | 1e8 | 0 | 5.7e-16 |
| 20 | 1e10 | 0 | 6.9e-16 |
| 40 | 1e12 | 0 | 1.4e-15 |
| 100 | 1e14 | 0 | 1.1e-14 |

The conversion is exact to the rounding of double precision on these
networks. The ill-conditioning reported in the literature didn't appear
here; it may on networks with very close or very many time constants.

## LTspice models

The LTspice models of each sample file were written by the command line and
their two test benches simulated with ngspice 42, which reads the same
netlists. The simulated rise $V(T) - V(T_{AMB})$ was compared with the
Foster formula $\sum R_k (1 - e^{-t/\tau_k})$, from 100 times the rise time
of the step to the end:

| File | Cells | Largest error / $R_{th}$, Foster model | Largest error / $R_{th}$, Cauer model |
|---|---|---|---|
| `LTSPICE_MOD1_1RC.xlsx` | 1 | 4.8e-4 | 4.8e-4 |
| `LTSPICE_MOD2_3RC.xlsx` | 3 | 3.9e-3 | 2.9e-3 |
| `LTSPICE_MOD3_5RC.xlsx` | 4 | 2.4e-3 | 8.3e-4 |
| `LTSPICE_IGBT.xlsx` | 4 | 1.2e-3 | 3.9e-4 |
| `RECONS_IGBT_100PTS.xlsx` | 4 | 1.2e-3 | 3.9e-4 |
| `MEAS_C2M0040120_TIM.xlsx` | 5 | 1.4e-3 | 4.6e-4 |
| `MEAS_C2M0040120_WATER.xlsx` | 6 | 2.0e-3 | 8.3e-4 |
| `MEAS_CPW5.xlsx` | 7 | 2.2e-3 | 8.8e-4 |
| `MEAS_DIODE.xlsx` | 5 | 1.5e-3 | 5.2e-4 |
| `MEAS_IGBT.xlsx` | 7 | 1.2e-3 | 3.9e-4 |

The error, below 0.4 % of $R_{th}$, comes from the time steps that the
simulator chooses, which differ between the two test benches; at the end
time, both simulated rises equal the formula to 6 significant digits. The
other `RECONS_IGBT_*PTS` files give the same network and errors up to
1.2e-3. When the two subcircuits are simulated in the same netlist, with the
same time steps, their curves agree to 1e-8 of $R_{th}$, which confirms the
conversion.

## Structure functions of the window

The window computes the structure functions with PyRth on a Foster curve
rebuilt from the first measured time, or from $t_{end}/10^6$ if earlier
(see [In the window](method.md#in-the-window)). The last $R_\Sigma$ should
equal the thermal resistance, the sum of the Foster $R_k$:

| File | Sum of the Foster $R_k$ (K/W) | Last $R_\Sigma$ (K/W) | Last $R_\Sigma$ with `GUI_STRUCTURE_FROM_FIRST_TIME = False` (K/W) |
|---|---|---|---|
| `MEAS_C2M0040120_TIM.xlsx` | 1.3671 | 1.3523 | 1.2813 |
| `MEAS_C2M0040120_WATER.xlsx` | 0.5900 | 0.5903 | 0.5833 |
| `MEAS_CPW5.xlsx` | 0.1920 | 0.1921 | 0.1605 |
| `MEAS_DIODE.xlsx` | 0.1039 | 0.1044 | 0.1034 |
| `MEAS_IGBT.xlsx` | 0.0843 | 0.0844 | 0.0772 |

The last $R_\Sigma$ is within 1.1 % of the thermal resistance on the five
measurements. With the time window of Zth_to_Foster (last column), the
structure function lost the cells faster than $t_{end}/10^6$: up to 16 % of
the thermal resistance on `MEAS_CPW5.xlsx`.

## Checks for every run

1. The input curve ends on a plateau.
2. The Foster curve lies on the input curve over the whole time range.
3. The Foster resistances add up to the last value of $Z_{th}$.
4. No time constant lies far outside the measured time range.
5. The last $R_\Sigma$ of the structure functions equals $R_{th}$ within
   about 1 %.
