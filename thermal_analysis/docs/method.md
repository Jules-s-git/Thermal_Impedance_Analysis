# How the identification works

This page describes what the tool computes at each step, why, and where the
method stops working. Each section starts with what the code does, then
explains the choice. The window and the command line run the same chain,
`pipeline.analyse`. The settings are listed in
[Settings and switches](reference.md#settings-and-switches), and the
functions in the [Code reference](api.md).

The main points, in short:

- The tool reads $Z_{th}(t)$ in log time, $z = \ln t$, where its derivative is
  the time-constant spectrum blurred by a fixed kernel.
- It removes the blur by Richardson-Lucy deconvolution. The number of
  iterations, M, is chosen by the data: the tool keeps the M whose Foster
  network fits $Z_{th}$ best.
- Each peak of the spectrum becomes one Foster cell. A scan of the time
  constants and a joint least-squares fit then refine the cells, and add
  cells where the fit is poor.
- `foster_to_cauer` converts the Foster network into the equivalent Cauer
  network. The command line computes the structure functions from it; the
  window computes them with PyRth, on a smooth curve rebuilt from the Foster
  network.

```text
Zth(t)
  │  1. dZ_dln_t                         derivative in log time, smoothed
  ▼
dZth/dz
  │  2. my_deconv (M iterations)         Richardson-Lucy deconvolution
  ▼
spectrum R(z)
  │  3. detect_min_max                   one cell per peak
  ▼
Foster network ── 4. repeat 2-3 for M = 1 ... 300, keep the best fit
  │  5. optimize_tau_sequential_parallel  scan of each time constant
  │  6. refine_foster_least_squares       joint fit, cells added if needed
  ▼
final Foster network (Rk, τk)
  │  7. foster_to_cauer                   window and command line
  ▼
Cauer network (Ri, Ci)
  │  8. cumulative_structure_function,    command line
  │     PyRth on the rebuilt Zth          window
  ▼
structure functions
```

## Thermal impedance

The thermal impedance is the temperature rise per watt after a power step.
When a constant power $P$ starts at t = 0 in a device, its junction
temperature rises from $T_j(0)$, and

$$
Z_{th}(t) = \frac{T_j(t) - T_j(0)}{P}
$$

$Z_{th}$ grows from 0 to the thermal resistance
$R_{th} = Z_{th}(\infty)$. A measurement often records the cooling after a
long heating instead; for a linear system the cooling curve gives the same
$Z_{th}$, as $(T_j(0) - T_j(t))/P$ (JEDEC JESD51-14).

The tool works on $Z_{th}$ only: it doesn't know the power, the device or how
the curve was obtained. It assumes that the system is linear (properties
independent of temperature) and that the curve starts at the power step.

## Foster and Cauer networks

Two RC networks of $n$ cells give the same kind of impedance.

![Two RC circuits driven by a current source P from ground into a node Tj. Left, the Foster network: three cells in series, each a resistor with a capacitor in parallel, the last one to the ambient ground. Right, the Cauer network: a ladder with resistors R1, R2, R3 in series from Tj to the ambient ground, and capacitors C1, C2, C3 from each node to ground.](figures/networks.png)

*Electrical analogy: the dissipated power $P$ is a current source, and the voltage of node $T_j$ with respect to the ambient node is the junction temperature rise $T_j - T_{amb}$.*

**Foster network.** Cells in series, each a resistance $R_k$ in parallel with
a capacitance $C_k$:

$$
Z_{th}(t) = \sum_{k=1}^{n} R_k \left(1 - e^{-t/\tau_k}\right), \qquad
\tau_k = R_k C_k
$$

It is the direct form of a sum of exponentials.
Its inner nodes have no physical meaning: a capacitance across a resistance
doesn't exist in the device, where all heat capacities are referred to the
ambient. The tool fits and reports this form, as $(R_k, \tau_k)$.

**Cauer network.** A ladder: resistances $R_i$ in series, with capacitances
$C_i$ from each node to the ambient. It is the discrete form of a
one-dimensional heat path, each cell being a slice of material: the heat
passes through $R_1$, part of it is stored in $C_2$, and so on. Its nodes
are temperatures, so it can be connected to a heat sink model.

Both forms describe the same impedance and can be converted into each other
(see [Foster to Cauer conversion](#foster-to-cauer-conversion)). The
element values differ: $R_1$ of the Foster network has nothing to
do with $R_1$ of the Cauer network.

## The time-constant spectrum

A real device has a continuous range of time constants, not a few separate
ones. With $\zeta = \ln \tau$, its impedance is a sum of first-order
responses weighted by a time-constant spectrum $R(\zeta)$
([Székely 1997](references.md)):

$$
Z_{th}(t) = \int R(\zeta)\left(1 - e^{-t/e^{\zeta}}\right) d\zeta
$$

$R(\zeta)\,d\zeta$ is the thermal resistance of the parts of the heat path
whose time constants lie between $\zeta$ and $\zeta + d\zeta$. A Foster
network is a spectrum made of separate spikes.

With $z = \ln t$, the derivative of $Z_{th}$ is a convolution of the
spectrum with a fixed kernel $w$:

$$
\frac{dZ_{th}}{dz}(z) = \int R(\zeta)\, w(z - \zeta)\, d\zeta,
\qquad w(x) = e^{\,x - e^{x}}
$$

$w$ is the derivative of one cell, $1 - e^{-t/\tau}$, with respect to
$\ln t$. It is a lopsided bell about one decade wide, with its peak at
$t = \tau$. Each time constant therefore shows as a bump of the derivative,
and close time constants merge. Finding $R(\zeta)$ is a deconvolution. This
is also why the input should be sampled uniformly in $\ln t$.

## Steps of the identification

The figure shows the steps on a synthetic curve whose Foster network is
known: the four-cell IGBT network of the `RECONS_IGBT_*.xlsx` files, sampled
at 20 points per decade.

![Three plots. 1: the input thermal impedance and the identified Foster curve on top of each other, from 5e-5 s to 50 s. 2: its derivative in log time, with two clear peaks and two shoulders. 3: the deconvolved spectrum with four sharp peaks, each at one of the four true time constants shown as dotted lines.](figures/nid_steps.png)

*The four time constants appear as four peaks of the spectrum, and the identified Foster curve lies on the input curve. Generated by `docs/_scripts/make_figures.py`.*

### 1. Derivative in log time

`dZ_dln_t` takes the finite differences of $Z_{th}$ with respect to
$\ln t$, smooths them with a Savitzky-Golay filter (window 5 points,
order 2), and puts a zero in front, so that the output keeps the length of
the input. Each difference is stored at the later of its two points.

A derivative amplifies noise. The light filter removes the point-to-point
jitter of a measurement and keeps the peaks. On a curve with fewer than 6
points, the filter is skipped.

### 2. Richardson-Lucy deconvolution

`my_deconv` solves $d = A\,R$, where $d$ is the derivative,
$A_{ij} = w(z_i - z_j)$ with each column scaled to a sum of 1, and $R$ the
spectrum on the same grid. It starts from a small constant,
$R_j = 10^{-6}$, and repeats M times
([Richardson 1972](references.md), [Lucy 1974](references.md)):

$$
R_j^{(m+1)} = R_j^{(m)} \sum_i A_{ij}\, \frac{d_i}{\left(A R^{(m)}\right)_i}
$$

The update multiplies, so the spectrum stays positive, as a passive heat
path requires. Each value is kept between 0 and $10^6$. The first point,
the padded zero of step 1, is left out of the sums.

The number of iterations M is the only setting and acts as the
regularisation. Few iterations give a smooth spectrum with merged peaks;
many give sharp peaks, and on noisy data, spurious ones.

![The spectrum of the same synthetic curve after 3, 30 and 300 iterations, with the four true time constants as dotted lines. After 3 iterations the spectrum is a broad hump; after 30, four peaks start to separate; after 300, four sharp peaks sit on the true time constants.](figures/effect_of_m.png)

*More iterations separate the time constants. On noisy data, too many iterations also turn noise into peaks: step 4 chooses M.*

### 3. From spectrum to Foster cells

`detect_min_max` turns the spectrum into Foster cells:

1. It finds the local maxima of the spectrum, and the local minima between
   them, plus the first and last non-zero points.
2. For each maximum, it integrates the spectrum over $z$ between the two
   neighbouring minima (trapezoidal rule). The area is the resistance $R_k$
   of one cell.
3. The time constant $\tau_k$ is the position of the peak, refined by a
   parabola through the peak and its two neighbours.
4. It scales the $R_k$ so that $\sum R_k = Z_{th}(t_{end})$, the last
   measured value.
5. It adjusts the $R_k$, with the $\tau_k$ fixed, to minimise the sum of the
   absolute differences between the rebuilt and the measured $Z_{th}$
   (L-BFGS-B, with $R_k \ge 10^{-12}$ K/W).

### 4. Choice of M

`optimize_M_range_parallel` repeats steps 2 and 3 for many values of M and
keeps the one whose Foster network has the smallest sum of absolute errors
on $Z_{th}$:

1. coarse search: M = 1, 11, 21, ..., 291;
2. fine search: every second value within ±10 of the best coarse M (for
   example 41, 43, ..., 61 around 51).

The values are tested in parallel threads. The data choose the
regularisation, not the user. The window doesn't show the chosen M; the
command line doesn't write it either.

### 5. Scan of the time constants

`optimize_tau_sequential_parallel` takes the cells one after the other, in
the order of the table, and multiplies the time constant of that cell by
every factor from 0.40 to 2.00 in steps of 0.01, the other cells being
fixed. It keeps the factor with the smallest sum of absolute errors. This
corrects the peak positions, which the deconvolution blurs and shifts when
peaks overlap. The resistances don't change in this step.

### 6. Joint least squares

`refine_foster_least_squares` fits all $R_k$ and $\tau_k$ together, by least
squares on $Z_{th}$ (SciPy trust region reflective method, with
$R_k, \tau_k \ge 10^{-12}$, tolerances $10^{-10}$, at most 2000 evaluations).

Then it checks the root mean square error, divided by the range of
$Z_{th}$. While it is above 0.2 %, it adds a cell and fits again:

- the new cell sits at the time of the largest error, with
  $R = |error| / (1 - e^{-1})$;
- it stops when the network reaches the *maximum number of Foster branches*
  (10 by default), or when the new cell would be more than $10^5$ times
  smaller than the largest one.

Two details matter in practice:

- If the deconvolution already gave more cells than the maximum, the joint
  fit is skipped and the network of step 5 is kept, with more cells than
  the maximum. The maximum only limits the cells that this step adds.
- Cells with $R_k < 10^{-6}$ K/W are removed at the end, as parasitic
  cells of the fit (switch `FILTER_SMALL_POLES` of `config.py`). On
  `LTSPICE_MOD2_3RC.xlsx`, this removes a fourth cell of $10^{-10}$ K/W.

The added cells go at the end of the table, which is why the table isn't
sorted by time constant.

## Foster to Cauer conversion

`foster_to_cauer` writes the Foster impedance as a ratio of two polynomials
in $s$,

$$
Z(s) = \sum_{k} \frac{R_k}{1 + R_k C_k s} = \frac{N(s)}{D(s)}
$$

then expands it as a continued fraction
([Székely and Van Bien 1988](references.md)):

$$
Z(s) = \cfrac{1}{s C_1 + \cfrac{1}{R_1 + \cfrac{1}{s C_2 + \dots}}}
$$

Each division by the highest power of $s$ gives one $C_i$, then one $R_i$.
The result is a ladder with as many cells as the Foster network, and the same
total resistance. The tool then keeps only the cells with $R_i > 0$ and
$C_i > 0$ (`cauer_structure_function_max_test`).

This division is known to be badly conditioned with many cells spread over
many decades ([Ziegeler et al. 2024](references.md)). In the tests of
[Validation](validation.md#foster-to-cauer-conversion), up to 100 cells over
14 decades, it reproduced the impedance to $10^{-14}$ of $R_{th}$, with no
negative element. Larger networks weren't tested.

The window and the command line both show this Cauer network (in the
stand-alone Zth_to_Foster tool, the window showed the Foster network instead;
switch `GUI_CONVERT_TO_CAUER`).

## Structure functions

The cumulative structure function plots the thermal capacitance accumulated
from the junction, $C_\Sigma$, against the thermal resistance accumulated
from the junction, $R_\Sigma$, along the heat path of a Cauer network
([Székely and Van Bien 1988](references.md);
[Poppe and Parry 2016](references.md)):

$$
R_\Sigma(n) = \sum_{i=1}^{n} R_i, \qquad C_\Sigma(n) = \sum_{i=1}^{n} C_i
$$

The differential structure function is its slope,
$K = dC_\Sigma / dR_\Sigma$, in W²·s/K². For a slice of material of
conductivity $\lambda$, specific heat $c$, density $\rho$ and cross-section
$A$, $K = c\,\rho\,\lambda\,A^2$: it grows with the area that the heat
crosses.

How to read them:

- a flat part of the cumulative function (a low $K$) is a region with a
  large resistance and little heat storage: a die attach, a thermal
  interface material;
- a steep part (a high $K$) is a region that stores much heat for little
  resistance, where the heat spreads: a base plate, a heat sink;
- the boundary between two regions is a change of slope, or a peak of the
  differential function. JESD51-14 uses the point where two curves of the
  same device, measured with two different interfaces, separate to find the
  junction-to-case resistance.

Structure functions describe one heat path from one source. They are
meaningful for the self-heating of a device, not for a coupling impedance
between two devices.

![Two plots of the structure functions of the four-cell IGBT network, computed as the command line does. Left: cumulative capacitance on a log axis against cumulative resistance, a staircase of four steps ending at the total resistance 0.084 K/W. Right: the differential function, three points rising from about 160 to 8700 W²s/K².](figures/structure_functions.png)

*Structure functions of the four-cell network, from its Cauer network. With few cells, they are staircases with few points.*

### In the command line

The command line converts the final Foster network with `foster_to_cauer`,
then:

1. `cumulative_structure_function` takes the cumulative sums of $R_i$ and
   $C_i$;
2. `filter_cumulative_min_resistance` drops the points with
   $R_\Sigma < 10^{-6}$ K/W;
3. `differential_structure_function` takes the finite differences
   $\Delta C_\Sigma / \Delta R_\Sigma$ between consecutive points, places
   them at the midpoints of $R_\Sigma$, and keeps the positive ones.

The structure functions have as many points as the Foster network has
cells, so they are coarse: a 7-cell network gives 7 cumulative points and
6 differential points.

### In the window

The window shows the same Cauer network as the command line, but computes
the structure functions with PyRth ([Ziegeler](references.md)), on a
smooth curve rebuilt from the Foster network:

1. `generate_foster_signal` rebuilds $Z_{th}$ from the Foster network on
   500 points, logarithmically spaced from $t_{start}$ to $t_{end}$, where
   $t_{end}$ is the last measured time and $t_{start}$ the earlier of the
   first measured time and $t_{end}/10^6$;
2. PyRth `standard_module` (Bayesian deconvolution, other settings at the
   PyRth defaults) computes a Cauer network from it and returns its
   cumulative sums, `int_cau_res` and `int_cau_cap`;
3. the points with $R_\Sigma$ below the smallest Foster resistance are
   dropped;
4. the differential function is computed as in the command line;
5. NaN values become 0, and infinite values $\pm 10^{20}$.

This gives smooth curves with about 200 points, which end at the measured
$R_{th}$: 0.0844 K/W on `MEAS_IGBT.xlsx`, for a Foster network of 0.0843 K/W
(see [Validation](validation.md#structure-functions-of-the-window)).

The start of the rebuilt curve matters. A Foster cell much faster than
$t_{start}$ has already settled at the first rebuilt point, so PyRth can't
see it and the structure function loses its resistance. The stand-alone
Zth_to_Foster tool started at $t_{end}/10^6$ only, which cut the cells of the
first microseconds on long measurements: on `MEAS_IGBT.xlsx` its structure
function ended at 0.077 K/W (switch `GUI_STRUCTURE_FROM_FIRST_TIME`).

## Limits of the method

**Time window.** The tool can only find time constants inside the measured
time range. A cell much faster than the first point is already settled and
shows as an offset of the first value; a cell much slower than the last
point hasn't started. If the curve doesn't end on a plateau, $R_{th}$ is
wrong: step 3 scales the resistances to the last measured value.

**Sampling.** The deconvolution works on the grid of the input. Uniform
sampling in $\ln t$ works best; 10 to 20 points per decade are enough (the
four-cell network is found exactly from 8 points per decade).
Linear sampling puts most points at long times and few at short times, and
the computation time grows with the square of the number of points (see
[Resample a long or linear curve](howto.md#resample-a-long-or-linear-curve)).

**Resolution.** In the spectrum, two time constants less than about half a
decade apart merge into one peak. The joint fit of step 6 separates them
again only if one cell leaves a root mean square error above 0.2 %. On a
noise-free curve of two equal cells, the spectrum showed one peak for a
ratio of 2 or 3 between the time constants, and the joint fit found both
cells exactly. On the 5-cell LTspice file, the tool finds 4 cells that fit
the curve within 0.07 % (see [Validation](validation.md)): a fit with fewer
cells isn't wrong, but its cells aren't the physical ones.

**Non-uniqueness.** Many Foster networks fit the same curve within the
measurement noise. The cells of a Foster network are a good model of
$Z_{th}$, not a measurement of the device structure. Use the structure
functions, not the Foster cells, to discuss layers.

**Positive cells only.** All $R_k$ and $\tau_k$ are positive. Such a network
always starts with a non-zero slope and stays concave in linear time. It
can't follow the delayed start of a coupling impedance between two devices;
the fit then has an error at short times.

**Linearity.** The method assumes constant material properties. Silicon and
SiC conductivities fall with temperature, and natural convection depends on
the temperature rise: the identified network is valid near the operating
point of the measurement.
