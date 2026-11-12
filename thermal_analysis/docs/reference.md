# Window, command line and files

Reference for every control of the window, every option of the command line,
every file format and every setting of the identification. For a guided
first run, see [Tutorial: first analysis of an IGBT measurement](tutorial.md).

## Main window

Start it with `python -m thermal_analysis` from the folder that contains
`thermal_analysis`, or by running `thermal_analysis/__main__.py` from any
folder. The window has three parts: controls on the left, plots in the
middle, result tables on the right.

### Controls

| Control | What it does |
|---|---|
| *Paste your data (time, Zth)* | Data box. Holds the curve as text, one point per line, time and $Z_{th}$ separated by tabs or spaces. The first line is always skipped as a header. An orange frame means that the data changed since the last *Process*. |
| *Maximum number of Foster branches* | Integer, 10 by default. Limit on the cells added by the least-squares step (see [6. Joint least squares](method.md#6-joint-least-squares)). |
| *Load File* | Opens an `.xlsx`, `.csv` or `.txt` file and copies its first two columns into the data box (see [Input formats](#input-formats)). |
| *Process* | Reads the data box and runs the whole identification. The window doesn't respond until it ends, 10 to 30 s for 126 points depending on the computer. |
| *Copy All Data* | Copies every result to the clipboard as tab-separated text (see [Exported files](#exported-files)). |
| *Export All Data* | Saves every result as an Excel workbook, one sheet per table (see [Excel workbook](#excel-workbook)). Choose the *CSV files* type, or type a name ending in `.csv`, to get the single-table CSV file instead (see [CSV export](#csv-export)). |
| *Export PDF* | Saves the five plots and all tables as a `.pdf` file. |
| *Export LTspice* | Asks for a folder and writes in it the LTspice models of the Foster and Cauer networks, each with its symbol and its test bench (see [LTspice models](#ltspice-models)). |
| *Edit Foster Poles* | Table of the Foster cells, `Rth_foster` (K/W) and `tau_foster` (s). Double-click a value to edit it; an edited row turns orange. |
| *Add Pole* | Adds a row `0.0 0.0` to the table. |
| *Update Foster Model* | Rebuilds the Foster curve from the table and redraws the plots. Nothing else is recomputed (see [Edit the Foster poles by hand](howto.md#edit-the-foster-poles-by-hand)). |

### Tabs

| Tab | Shows |
|---|---|
| *Zth* | Measured $Z_{th}$ (solid) and Foster curve (dashed), against time on a log axis. |
| *dZ/dln(t)* | Derivative of the measured curve and of the Foster curve, against $\ln t$. |
| *Spectrum R* | Time-constant spectrum of the measured curve and of the Foster curve, against $\ln t$, both with the chosen M. |
| *Structure (Cumulative)* | $C_\Sigma$ (J/K, log axis) against $R_\Sigma$ (K/W). A red line marks the last $R_\Sigma$, with its value. |
| *Structure (Differential)* | $dC_\Sigma/dR_\Sigma$ (W²·s/K², log axis) against $R_\Sigma$. |
| *Notice* | Short explanations of the Foster and Cauer models and of the structure functions, with pictures. |

Each plot has the Matplotlib toolbar: zoom, pan, and save the plot as an
image.

### Result tables

| Table | Columns | Content |
|---|---|---|
| *Foster (Rth_foster, tau_foster)* | K/W, s | final Foster network, in the order of the identification |
| *Cauer (Rth_cauer, C_cauer)* | K/W, J/K | Cauer network equivalent to the Foster network, from the junction to the ambient |
| *Cumulative SF (RΣ, CΣ)* | K/W, J/K | cumulative structure function from PyRth, about 200 points |
| *Differential SF (RΣ, dC/dR)* | K/W, W²·s/K² | differential structure function |

Each table has a *Copy* button. The tables show 6 significant digits.

### Status messages

The status line, at the bottom left, shows:

| Message | Meaning |
|---|---|
| `File: None` / `File: <name>` | No file loaded / name of the last loaded file. Pasted data doesn't change it. |
| `Running PyRth evaluation...` | *Process* started. |
| `Optimizing M values (parallel)...` | Choice of M, steps 2 to 4 of the method. |
| `Optimizing tau values (parallel)...` | Scan of the time constants. |
| `Refining Foster fit (global least-squares)...` | Joint least squares, then structure functions. |
| `Processed successfully` | All results are up to date. |
| `Foster model updated` | *Update Foster Model* done. |
| `Data exported: <name>` | *Export All Data* done. |
| `PDF exported: <path>` | *Export PDF* done. |
| `LTspice models exported: <NAME>_FOSTER, <NAME>_CAUER` | *Export LTspice* done. |

Errors open a dialog with the Python message. The common ones are in
[Troubleshooting](troubleshooting.md).

## Command line

Start it with the command of the window followed by `-file` and the input
file. The command depends on the current folder:

| Current folder | Window | Command line |
|---|---|---|
| the folder that contains `thermal_analysis` | `python -m thermal_analysis` | `python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx` |
| the `thermal_analysis` folder itself | `python __main__.py` | `python __main__.py -file input_data/MEAS_IGBT.xlsx` |
| any other folder | `python <path>/thermal_analysis/__main__.py` | `python <path>/thermal_analysis/__main__.py -file <path>/MEAS_IGBT.xlsx` |

`python -m thermal_analysis.cli` and `python cli.py` (inside the folder) do
the same. With arguments, `__main__.py` starts the command line instead of
the window. With `-nfb`:

```bash
python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx -nfb 8
```

`python __main__.py -h` shows the options. In its usage line,
`[-nfb N]` means that `-nfb` is optional: type `-nfb 8`, without the
brackets.

| Option | Meaning |
|---|---|
| `-file`, `--datafile` | Input file, required. `.xlsx`, `.csv`, or any other extension read as plain text (see [Input formats](#input-formats)). |
| `-nfb`, `--n_foster_branches` | Maximum number of Foster branches, 10 by default. Same meaning as in the window. |
| `-h`, `--help` | Shows the options. |

The command line runs the same identification as the window
(`pipeline.analyse`), without PyRth, and computes the structure functions
from the Cauer network (see [In the command line](method.md#in-the-command-line)).
When it succeeds, it prints the progress messages, the name of the Excel
workbook and the names of the LTspice files. A missing input file, an
unknown argument or brackets typed from the usage line stop it with a
message that says so. It writes its files in the current folder and
overwrites them without warning.

| File | Content |
|---|---|
| `foster.txt` | Foster network: `Rth_foster` (K/W), `tau_foster` (s), one cell per line |
| `cauer.txt` | Cauer network: `Rth_cauer` (K/W), `C_cauer` (J/K), from the junction to the ambient |
| `cumul.txt` | cumulative structure function: `R_cum` (K/W), `C_cum` (J/K) |
| `diff.txt` | differential structure function: `Rdiff` (K/W), `dC_dR` (W²·s/K²) |
| `zth_plot.txt` | Python script that plots the input $Z_{th}$ |
| `dz_plot.txt` | Python script that plots $dZ_{th}/d\ln t$ against $\ln t$ |
| `spectrum_plot.txt` | Python script that plots $dZ_{th}/d\ln t$ against time. Despite its title, *Spectrum R*, it doesn't plot the spectrum. |
| `cumul_plot.txt` | Python script that plots the cumulative structure function |
| `diff_plot.txt` | Python script that plots the differential structure function |
| `<NAME>_results.xlsx` | Excel workbook of all results, one sheet per table (see [Excel workbook](#excel-workbook)) |
| `<NAME>_FOSTER.net`, `<NAME>_CAUER.net` | LTspice models of the Foster and Cauer networks |
| `<NAME>_FOSTER.asy`, `<NAME>_CAUER.asy` | LTspice symbols of the two models |
| `<NAME>_FOSTER_testbench.net`, `<NAME>_CAUER_testbench.net` | LTspice test benches: power step on each model |

`<NAME>` is the name of the input file without its extension, in upper case,
with every character other than a letter, a digit or `_` replaced by `_`:
`MEAS_IGBT.xlsx` gives `MEAS_IGBT`. The six LTspice files are described in
[LTspice models](#ltspice-models). In `config.py`, `EXCEL_EXPORT = False`
turns the workbook off and `CLI_WRITE_LTSPICE = False` the LTspice files.

The four tables are text files written by `numpy.savetxt`: a header line
starting with `#`, then two numbers per line separated by a space, with 19
significant digits. They load back with `numpy.loadtxt`. The `*_plot.txt`
files are Python code with the data inside; run them with
`python zth_plot.txt`.

## Input formats

| Source | How it is read | Header line | Columns |
|---|---|---|---|
| *Load File*, `.xlsx` | `pandas.read_excel`, first sheet | required (first row) | first two |
| *Load File*, `.csv` | `pandas.read_csv`, comma-separated | required | first two |
| *Load File*, `.txt` | `pandas.read_csv`, tab-separated | required | first two |
| Data box (pasted text) | split on spaces and tabs, decimal commas replaced by points | first line always skipped | first two |
| Command line, `.xlsx` | `pandas.read_excel`, first sheet | required | `time` and `Zth` if present, otherwise the first two |
| Command line, `.csv` | `pandas.read_csv`, comma-separated | required | `time` and `Zth` if present, otherwise the first two |
| Command line, other extension | `numpy.loadtxt`, spaces or tabs | not allowed (a line starting with `#` is ignored) | first two |

In every case:

- time is in seconds and $Z_{th}$ in K/W (any unit works, but the labels and
  units of the results assume these);
- points with a time of 0 or less are dropped;
- times must be strictly increasing;
- in the window, *Load File* copies the data into the data box, and
  *Process* then reads the box, not the file.

## Exported files

### Excel workbook

*Export All Data* (window) and the command line (`<NAME>_results.xlsx`)
write an Excel workbook with one sheet per table. Each table keeps its own
length, so nothing is padded or cut, and the values keep full precision
(shown with 7 significant digits). The first row of each sheet holds the
column names with their units and stays visible when you scroll.

| Sheet | Columns | Content |
|---|---|---|
| *Summary* | `Quantity`, `Value`, `Unit` | input file, number of points, first and last time, last $Z_{th}$, number of Foster and Cauer cells, $R_{th}$ (sum of the Foster $R_k$), M |
| *Zth* | `time (s)`, `Z_meas (K/W)`, `Z_foster (K/W)` | input curve and Foster curve, one row per time point |
| *Foster* | `cell`, `Rth_foster (K/W)`, `tau_foster (s)`, `C_foster (J/K)` | Foster network, fastest cell first, $C_k = \tau_k / R_k$ |
| *Cauer* | `cell`, `R_cauer (K/W)`, `C_cauer (J/K)` | Cauer network, from the junction to the ambient |
| *Cumulative SF* | `R_cum (K/W)`, `C_cum (J/K)` | cumulative structure function |
| *Differential SF* | `R_diff (K/W)`, `dC/dR (W²·s/K²)` | differential structure function |

In the window, after *Update Foster Model*, the *Summary*, *Zth* and
*Foster* sheets hold the edited network; the other sheets follow the last *Process*.

### CSV export

*Export All Data* with a `.csv` name writes one comma-separated file, and
*Copy All Data* the same table as tab-separated text, with these columns:

| Column | Unit | Content |
|---|---|---|
| `time` | s | time of each point |
| `Z_meas` | K/W | input $Z_{th}$ |
| `Z_foster` | K/W | $Z_{th}$ rebuilt from the Foster network |
| `Rth_foster`, `tau_foster` | K/W, s | Foster network |
| `R_cauer`, `C_cauer` | K/W, J/K | Cauer network |
| `Rth_cum`, `C_cum` | K/W, J/K | cumulative structure function |
| `Rth_diff` | K/W | $R_\Sigma$ of the differential structure function |
| `dC/dR` (file) or `dC_dR` (clipboard) | W²·s/K² | differential structure function |

All columns have the length of `time`. Shorter columns are padded by
repeating their last value; longer columns are cut (see
[Export the results](howto.md#export-the-results)). The file holds full
precision.

### PDF report

*Export PDF* writes, in this order:

1. $Z_{th}$, measured and Foster;
2. the derivative in log time, measured only;
3. the spectrum, measured only;
4. the cumulative structure function, on log-log axes;
5. the differential structure function, as steps on log-log axes;
6. then tables: Foster network, *Cauer* table, cumulative and differential
   structure functions, and the data (`time`, `Z_meas`, `Z_foster`). Each
   table takes as many pages as needed, 50 rows per page, with values
   rounded to 6 decimals.

The structure function plots of the PDF use a log scale for $R_\Sigma$,
unlike the window.

### LTspice models

*Export LTspice* (window) and the command line write two LTspice models,
built as the model of kicad_icepak (v47): one for the Foster network, one for
the Cauer network. Each model has three files:

| File | Content |
|---|---|
| `<NAME>_<KIND>.net` | model: the subcircuit `.SUBCKT <NAME>_<KIND> P T TAMB`, with the values of the cells in comment lines |
| `<NAME>_<KIND>.asy` | LTspice symbol of the subcircuit; its `ModelFile` attribute points to `<NAME>_<KIND>.net` |
| `<NAME>_<KIND>_testbench.net` | test bench: includes the model, applies a power step and simulates up to the last measured time |

`<KIND>` is `FOSTER` or `CAUER`. In the window, `<NAME>` comes from the last
loaded file, or is `ZTH` when the data were pasted. The exported network is
the one of the *Edit Foster Poles* table after the last *Process* or
*Update Foster Model*; the Cauer model is converted from it when the files
are written.

**Electrical analogy.**

| Thermal | Electrical |
|---|---|
| power (W) | current (A) |
| temperature (°C) | voltage (V) |
| thermal resistance (K/W) | resistance (Ω) |
| heat capacity (J/K) | capacitance (F) |

**Pins.** Both models have the same three pins, in this order:

| Pin | Role |
|---|---|
| `P` | power input: the current that enters `P` is the dissipated power. A 0 V source `VSENSE` from `P` to `TAMB` measures it. |
| `T` | temperature output: $V(T) = V(T_{AMB}) + Z_{th} \ast P$ |
| `TAMB` | ambient or reference temperature |

**Inside the models.** A current-controlled current source `F1` copies
the current of `VSENSE` into the RC network. The voltage across the network
is the temperature rise; a voltage-controlled voltage source `E1` copies it
between `T` and `TAMB`. The inner nodes `N1`, `N2`, … connect to nothing
outside the subcircuit, so a load on `T` doesn't change the network.

- `<NAME>_FOSTER`: one $R_k \parallel C_k$ cell per Foster cell, in series
  from `N1` to `TAMB`, fastest cell first, with $C_k = \tau_k / R_k$.
- `<NAME>_CAUER`: the Cauer network computed by `foster_to_cauer`,
  junction first: $C_i$ from node $N_i$ to `TAMB`, $R_i$ from $N_i$ to
  $N_{i+1}$, the last resistance to `TAMB`. It has the same $Z_{th}(t)$ as
  the Foster model. If the conversion gives an element that isn't
  positive, the three Cauer files aren't written, and the window shows a
  warning.

Values are written with 9 significant digits. The files contain only ASCII
characters.

**Test benches.** `<NAME>_FOSTER_testbench.net` and
`<NAME>_CAUER_testbench.net` differ only by the model they include. Each
holds:

- `.include <NAME>_<KIND>.net`;
- `VAMB TAMB 0 25`: ambient at `LTSPICE_AMBIENT`, 25 °C;
- `IP 0 P PWL(0 0 <rise> 1)`: a step of
  `LTSPICE_TESTBENCH_POWER`, 1 W, which rises in $\tau_{min}/100$ rounded
  down to a decade, kept between 0.1 µs and 1 µs;
- `X1 P T TAMB <NAME>_<KIND>`: the model;
- `.tran` up to the last measured time, with a maximum time step of
  1/10000 of it;
- `.meas TRAN T_END FIND V(T)`: the temperature at the end time;
- `.options plotwinsize=0`, which turns off the waveform compression of
  LTspice.

With 1 W, $V(T) - V(T_{AMB})$ is $Z_{th}(t)$ in K/W.

## Settings and switches

Every number that drives the analysis is in `thermal_analysis/config.py`.
Change it there (see [Change a setting of the analysis](howto.md#change-a-setting-of-the-analysis));
none can be changed from the window, apart from the maximum number of
branches. The window and the command line use the same values.

### Switches

| Name in `config.py` | Default | Effect |
|---|---|---|
| `FILTER_SMALL_POLES`, `MIN_POLE_RESISTANCE` | `True`, 1e-6 | Remove the Foster cells with $R_k <$ 1e-6 K/W at the end of the least squares. |
| `GUI_CONVERT_TO_CAUER` | `True` | The window shows the Cauer network. `False`: it shows the Foster network in the *Cauer* table. |
| `GUI_STRUCTURE_FROM_FIRST_TIME` | `True` | The window rebuilds the Foster curve from the first measured time, or from $t_{end}/10^6$ if earlier. `False`: from $t_{end}/10^6$ only. |
| `GUI_RUN_UNUSED_PYRTH_LASSO` | `False` | `True`: run the PyRth lasso evaluation of Zth_to_Foster, whose result nothing uses. |
| `DIFFERENTIAL_UNIT_LABEL` | `"W²·s/K²"` | Unit written on the axis of the differential structure function. |
| `EXCEL_EXPORT` | `True` | *Export All Data* proposes an Excel workbook, and the command line writes `<NAME>_results.xlsx`. `False`: *Export All Data* proposes a CSV file, and the command line writes no workbook. |
| `CLI_WRITE_LTSPICE` | `True` | The command line also writes the six LTspice files. `False`: only the nine files of Zth_to_Foster. |

[Differences with Zth_to_Foster](differences.md) explains each switch and
its effect.

### Settings

| Step | Setting | Value | Name in `config.py`, or function |
|---|---|---|---|
| Input | times kept | $t > 0$ | `data_io.read_table`, `data_io.parse_text` |
| 1. Derivative | Savitzky-Golay window, order | 5 points, 2 | `dZ_dln_t` defaults |
| 1. Derivative | floor on $t$ before the logarithm | 1e-12 s | `safe_log_time` |
| 2. Deconvolution | start value, floor of the denominator | 1e-6, 1e-12 | `my_deconv` |
| 2. Deconvolution | range of the spectrum | 0 to 1e6 | `my_deconv` |
| 3. Cells | threshold of the non-zero spectrum | 1e-24 | `detect_min_max` |
| 3. Cells | fit of the resistances | L-BFGS-B, sum of absolute errors, $R_k \ge$ 1e-12 | `detect_min_max` |
| 4. Choice of M | range, fine step (coarse step: max(10, fine step)) | 1 to 300, 2 | `M_MIN`, `M_MAX`, `M_STEP` |
| 4. Choice of M | threads | all processors (-1) | `N_JOBS` |
| 5. Time constants | factors | 0.40 to 2.00, step 0.01 | `TAU_FACTOR_MIN`, `TAU_FACTOR_MAX`, `TAU_FACTOR_STEP` |
| 6. Least squares | maximum number of cells | 10, or the window entry / `-nfb` | `DEFAULT_MAX_BRANCHES` |
| 6. Least squares | target error | 0.2 % (root mean square error divided by the range of $Z_{th}$) | `max_error` of `refine_foster_least_squares` |
| 6. Least squares | solver | trust region reflective, tolerances 1e-10, 2000 evaluations, bounds 1e-12 | `refine_foster_least_squares` |
| 6. Least squares | stop when a new cell is smaller than | largest $R_k$ / 1e5 | `refine_foster_least_squares` |
| Cauer | cells kept | $R_i > 0$ and $C_i > 0$ | `cauer_structure_function_max_test` |
| Structure functions, command line | points kept | $R_\Sigma \ge$ 1e-6 K/W | `CLI_MIN_CUMULATIVE_RESISTANCE` |
| Structure functions, window | rebuilt curve | 500 points, from $t_{end}/10^6$ (or the first measured time if earlier) to $t_{end}$ | `SF_REBUILT_POINTS`, `SF_TIME_SPAN` |
| Structure functions, window | PyRth | `standard_module`, `deconv_mode="bayesian"`, other settings at PyRth defaults | `PYRTH_STANDARD` |
| Structure functions, window | points kept | $R_\Sigma \ge$ smallest Foster $R_k$ | `pipeline` |
| Structure functions, window | invalid values | NaN to 0, ±infinity to ±1e20 | `CLEAN_MAX_VALUE` |
| Differential function | values kept | positive only; 1e-12 added to each $\Delta R_\Sigma$ | `differential_structure_function` |
| LTspice models | name when the data were pasted | `ZTH` | `LTSPICE_DEFAULT_NAME` |
| LTspice models | power step and ambient of the test bench | 1 W, 25 °C | `LTSPICE_TESTBENCH_POWER`, `LTSPICE_AMBIENT` |
| Unused PyRth call (off) | lasso settings | `lasso_alpha=0.001`, `theo_time_size=500`, `log_time_size=100` | `PYRTH_LASSO` |

## Nomenclature

| Symbol | In the code | Meaning | Unit |
|---|---|---|---|
| $t$ | `time` | time since the power step | s |
| $z$ | `z` | $\ln t$ | — |
| $Z_{th}$ | `Z_meas` | input thermal impedance | K/W |
| $dZ_{th}/dz$ | `dZ_dz` | derivative in log time | K/W |
| $R(z)$ | `R_spec`, `R` | time-constant spectrum, resistance per unit of $\ln\tau$ | K/W |
| M | `M`, `M_opt` | number of Richardson-Lucy iterations | — |
| $R_k$, $\tau_k$, $C_k$ | `Rth_foster`, `tau_foster`, `C_foster` | Foster cell: resistance, time constant, capacitance $\tau_k/R_k$ | K/W, s, J/K |
| $n$ | `n_branches`, `max_poles` | number of cells (maximum) | — |
| $R_i$, $C_i$ | `Rth_cauer`, `C_cauer` | Cauer cell | K/W, J/K |
| $R_\Sigma$, $C_\Sigma$ | `Rth_cum`, `C_cum` | cumulative resistance and capacitance from the junction | K/W, J/K |
| $K = dC_\Sigma/dR_\Sigma$ | `dC_dRth`, `dC_dR` | differential structure function | W²·s/K² |
| $R_{th}$ | | thermal resistance, $Z_{th}(\infty)$ | K/W |

**Terms.** A *cell* is one RC pair of a network. The code and the window
also call a Foster cell a *pole* (the time constant $\tau_k$ is a pole of
$Z(s)$ at $s = -1/\tau_k$) or a *branch*; the three words mean the same
here.
