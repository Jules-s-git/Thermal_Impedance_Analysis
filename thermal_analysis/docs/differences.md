# Differences with Zth_to_Foster

The `thermal_analysis` package replaces the stand-alone Zth_to_Foster tool
(`main.py`, `gui.py`, `cli_main.py`, `functions.py`). It has the same
window, the same command line and the same identification. It differs on
five points and adds two outputs, the Excel workbook and the LTspice models.
Each of these seven changes has a switch in `thermal_analysis/config.py`,
except the *Export LTspice* button, which changes nothing else, so that you
can keep either behaviour. To get all the results of Zth_to_Foster
back at once, see
[Get the results of Zth_to_Foster back](howto.md#get-the-results-of-zth_to_foster-back).

## Removal of the parasitic poles

Switch `FILTER_SMALL_POLES` (with `MIN_POLE_RESISTANCE`), `True` by
default.

`refine_foster_least_squares` removes the Foster cells whose resistance is
below 1e-6 K/W, at the end of the fit, and also when it skips the fit
because the deconvolution gave more cells than the maximum. Zth_to_Foster
keeps them. This behaviour already existed in the earlier `thermal_analysis`
package of the KiCad/Icepak project.

On the sample files, it only changes `LTSPICE_MOD2_3RC.xlsx`: Zth_to_Foster
gives 4 cells, one of them of 1e-10 K/W; the package gives the 3 real cells.

## Cauer network in the window

Switch `GUI_CONVERT_TO_CAUER`, `True` by default.

The window converts the Foster network with `foster_to_cauer`, as the
command line does. In Zth_to_Foster, the *Cauer* table of the window (and the
`R_cauer`, `C_cauer` columns of the exports) repeated the Foster network,
with $C_k = \tau_k / R_k$, because the window never called the conversion.

On `MEAS_IGBT.xlsx`, the first Cauer cells are 0.00355 and 0.00396 K/W,
instead of the Foster values 0.00439 and 0.00426 K/W. Both networks add up
to 0.0843 K/W.

## Time window of the structure functions

Switch `GUI_STRUCTURE_FROM_FIRST_TIME`, `True` by default.

The window computes the structure functions with PyRth on a Foster curve
rebuilt from $t_{start}$ to $t_{end}$. The package starts at the first
measured time, or at $t_{end}/10^6$ if that is earlier. Zth_to_Foster always
started at $t_{end}/10^6$: on a measurement that lasts 850 s, that is
0.85 ms, and the cells faster than that were lost.

| File | Sum of the Foster $R_k$ (K/W) | Last $R_\Sigma$, package | Last $R_\Sigma$, Zth_to_Foster |
|---|---|---|---|
| `MEAS_C2M0040120_TIM.xlsx` | 1.3671 | 1.3523 | 1.2813 |
| `MEAS_C2M0040120_WATER.xlsx` | 0.5900 | 0.5903 | 0.5833 |
| `MEAS_CPW5.xlsx` | 0.1920 | 0.1921 | 0.1605 |
| `MEAS_DIODE.xlsx` | 0.1039 | 0.1044 | 0.1034 |
| `MEAS_IGBT.xlsx` | 0.0843 | 0.0844 | 0.0772 |

The start never moves later than in Zth_to_Foster, so a short curve (for
example `LTSPICE_MOD1_1RC.xlsx`, 3 decades) gives the same structure function
as before.

## Unused PyRth evaluation

Switch `GUI_RUN_UNUSED_PYRTH_LASSO`, `False` by default.

At the start of *Process*, Zth_to_Foster ran a PyRth evaluation with lasso
deconvolution on the measured data and never used its result. The package
skips it. No result changes; *Process* takes about 1.5 s less.

## Unit of the differential structure function

Switch `DIFFERENTIAL_UNIT_LABEL`, `"W²·s/K²"` by default.

The axis of the differential structure function, in the window and in the
PDF report, says W²·s/K², the unit of $dC_\Sigma/dR_\Sigma$:
(J/K) / (K/W). Zth_to_Foster wrote J/K².

## Excel workbook

Switch `EXCEL_EXPORT`, `True` by default.

*Export All Data* proposes an Excel workbook, with one sheet per table:
summary, $Z_{th}$, Foster, Cauer and both structure functions (see
[Excel workbook](reference.md#excel-workbook)). Each table keeps its own
length. Zth_to_Foster wrote only a CSV file, where every column was padded or
cut to the length of the time column. The CSV file is still available: choose
the *CSV files* type in the dialog. The command line also writes the
workbook, `<NAME>_results.xlsx`.

With `EXCEL_EXPORT = False`, *Export All Data* proposes a CSV file first and
the command line writes no workbook, as Zth_to_Foster.

## LTspice models

Switch `CLI_WRITE_LTSPICE`, `True` by default, for the command line.

The package writes the identified network as LTspice models, as
kicad_icepak does in v47: one model for the Foster network and one for the
Cauer network, each with the pins `P`, `T` and `TAMB`, its symbol and its
test bench (see [LTspice models](reference.md#ltspice-models)).
Zth_to_Foster had no LTspice output.

- The window has a new button, *Export LTspice*. It writes the files only
  when you click it.
- The command line writes the six files after its nine text files (and
  the workbook), and prints their names. With `CLI_WRITE_LTSPICE = False`, it writes only the
  nine files and prints nothing, as Zth_to_Foster.

## Changes without a switch

These change no result:

- **Starting the tool.** The window and the command line start from the
  package: `python -m thermal_analysis`, or by running
  `thermal_analysis/__main__.py`. Options, files, messages and window are
  those of `main.py` and `cli_main.py`; only the window title changes, to
  *Thermal Impedance Analysis tool*.
- **Messages of the command line.** The usage line shows the command as
  typed (`python __main__.py`, `python -m thermal_analysis`), and the
  command line stops with a clear message when the input file doesn't exist
  or an argument is unknown, for example `[-nfb N]` copied with its
  brackets. Zth_to_Foster stopped with a Python traceback on a missing file.
  The window shows *Data exported* after *Export All Data*.
- **Any folder.** The window finds the pictures of its *Notice* tab from the
  package; Zth_to_Foster had to be started from its own folder.
- **NumPy 2.** The computation uses `np.trapezoid` when NumPy has it, instead
  of `np.trapz`, which NumPy 2.5 no longer has. The command line therefore
  also runs with NumPy 2; the window still needs NumPy < 2 for PyRth.
- **One analysis function.** The window and the command line call the same
  `pipeline.analyse`, instead of two copies of the same steps, and read and
  write files through `data_io`.
- **Named settings.** The range of M, the factors of the scan of the time
  constants, the settings of PyRth and the other constants are named in
  `config.py` instead of being written in the calls.

## How the equivalence was checked

With the seven switches set to the values of Zth_to_Foster, the package was
compared with Zth_to_Foster on the sample files:

- command line, on `MEAS_IGBT.xlsx`, `MEAS_CPW5.xlsx`,
  `LTSPICE_MOD1_1RC.xlsx` and `LTSPICE_MOD2_3RC.xlsx`: the nine output
  files are identical, byte for byte;
- window, on `MEAS_IGBT.xlsx`: the four result tables, the CSV export and the
  text of the PDF report are identical.

With `FILTER_SMALL_POLES = True` only, the command line gives the same files
as the earlier `thermal_analysis` package. The window was then run with the
default settings on nine of the sample files (all but the larger copies of
the four-cell IGBT network), without error.
