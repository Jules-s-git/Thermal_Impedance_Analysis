# How-to guides

Short recipes for common tasks. Each one assumes you know the basic run of
the [Tutorial: first analysis of an IGBT measurement](tutorial.md).

## Prepare an input file

The tool reads one curve: time in seconds in the first column, $Z_{th}$ in
K/W in the second.

1. Put a header line first, for example `time` and `Zth`. The window, and
   the command line with `.xlsx` and `.csv` files, always read the first
   line as a header, even when it holds numbers.
2. Sort the rows by strictly increasing time. Remove duplicate times: the
   derivative divides by the time step.
3. Rows with a time of 0 or less are dropped. Keep the first point after the
   power step.
4. If you have a temperature $T_j(t)$ and a power step $P$, compute
   $Z_{th} = (T_j(t) - T_j(0)) / P$ first. The tool doesn't know the power.
5. Make sure the curve ends on a plateau: the tool scales the network to the
   last value (see [Limits of the method](method.md#limits-of-the-method)).
6. Save as `.xlsx` (first sheet) or as `.csv` with commas between the
   columns. These two formats work the same way in the window and in the
   command line.

A `.txt` file works too, but differently: the window reads it as
tab-separated with a header line, and the command line as separated by
spaces or tabs, **without** a header line. See
[Input formats](reference.md#input-formats).

## Paste data from a spreadsheet

1. In the spreadsheet, select the two columns, with their header line, and
   copy them.
2. In the window, click in the data box, delete its content, and paste.
3. Click *Process*.

The columns must be separated by tabs or spaces, which is what Excel and
LibreOffice copy. Decimal commas (`1,5E-03`) are accepted. Comma-separated
or semicolon-separated text isn't: each line becomes one value and is
ignored (see [IndexError: too many indices for array](troubleshooting.md#indexerror-too-many-indices-for-array)).

## Resample a long or linear curve

Use this when the curve has many points, or isn't spaced uniformly in log
time: an LTspice or Icepak export, or a measurement recorded at a fixed rate.
The computation time grows with the square of the number of points, and
linear sampling leaves few points at short times.

1. Save this script as `resample.py` next to your data:

   ```python
   import sys
   import numpy as np, pandas as pd

   src, dst, per_decade = sys.argv[1], sys.argv[2], int(sys.argv[3])
   df = pd.read_excel(src)
   t = df.iloc[:, 0].to_numpy(float)
   z = df.iloc[:, 1].to_numpy(float)
   keep = t > 0
   t, z = t[keep], z[keep]
   n = int(np.ceil(np.log10(t[-1] / t[0]) * per_decade)) + 1
   t_log = np.logspace(np.log10(t[0]), np.log10(t[-1]), n)
   z_log = np.interp(np.log(t_log), np.log(t), z)
   pd.DataFrame({"time": t_log, "Zth": z_log}).to_excel(dst, index=False)
   print(f"{len(t)} points -> {n} points")
   ```

2. Run it with 20 points per decade:

   ```bash
   python resample.py LTSPICE_IGBT.xlsx LTSPICE_IGBT_log.xlsx 20
   ```

3. Process the new file.

On `LTSPICE_IGBT.xlsx`, this takes the curve from 535 to 136 points and the
processing from 141 s to 7 s, with the same four cells within 1.5 %
(see [Validation](validation.md#four-cell-igbt-network-known-values)).
The linear interpolation in $\ln t$ adds a small error where the original
points are far apart: check the fit afterwards on the original file if you
need better than 0.1 %.

## Choose the maximum number of Foster branches

*Maximum number of Foster branches* (window) or `-nfb` (command line), 10 by
default, limits the cells that the least-squares step adds when the fit is
poor.

- Keep 10 for a first analysis. The sample files of `input_data` end with
  1 to 7 cells.
- Lower it to get a smaller network, for example for a fast circuit
  simulation. The fit gets worse where a cell is missing; check it in the
  *Zth* tab.
- Raise it if the fit is visibly poor and the network already has as many
  cells as the maximum.

The limit isn't strict: if the deconvolution alone finds more cells than the
maximum, the tool keeps them all and skips the least-squares step (see
[6. Joint least squares](method.md#6-joint-least-squares)).

## Edit the Foster poles by hand

Use this to try a network of your own, or to remove a cell you don't want.
Process the data first.

1. In the *Edit Foster Poles* table, double-click a value, type the new
   value, then click elsewhere. The row turns orange.
2. To add a cell, click *Add Pole*: a row `0.0 0.0` appears at the end. Set
   its resistance and time constant.
3. To remove a cell, set its resistance to 0. The table has no delete button.
4. Click *Update Foster Model*. The status says `Foster model updated` and
   the *Zth* tab shows the curve of the edited network.

Only the Foster curve and the Foster values used by the exports change,
including the LTspice models. The
*Foster* table on the right, the *Cauer* table, the structure functions and
the "reconstructed" curves of the *dZ/dln(t)* and *Spectrum R* tabs keep the
values of the last *Process*. Clicking *Process* again replaces your edits.

## Export the results

The window gives five ways to get the results out:

| Button | Gives | Format |
|---|---|---|
| *Copy* above a table | that table | tab-separated text, 6 significant digits, no header |
| *Copy All Data* | every result | tab-separated text with a header, to paste in a spreadsheet |
| *Export All Data* | every result | Excel workbook, one sheet per table; or, with a `.csv` name, one comma-separated table |
| *Export PDF* | five plots and all tables | `.pdf` file: five plot pages, then table pages |
| *Export LTspice* | Foster and Cauer networks as LTspice models | six files in a folder: model, symbol and test bench of each network (see [Export the network to LTspice](#export-the-network-to-ltspice)) |

The Excel workbook is the most convenient: each table is on its own sheet,
at its own length, with units in the column names (see
[Excel workbook](reference.md#excel-workbook)). The command line writes the
same workbook, `<NAME>_results.xlsx`.

In *Copy All Data* and in the CSV file, the results share one table, and
every column has the length of the time column, one row per time point:

- a shorter column, such as `Rth_foster` with 7 cells, is padded by
  repeating its last value. Only the first rows are the network: as many
  rows as the *Foster* table has;
- a longer column is cut. The structure functions of the window have about
  200 points: on a file with fewer time points, their end is lost. Use the
  *Copy* buttons of the structure function tables to get all their points.

The PDF tables round values to 6 decimals, so a time constant of
2.7847e-05 s shows as 2.8e-05. Use the Excel workbook for exact values.

The column names are listed in [Exported files](reference.md#exported-files).

## Get a Cauer network

After *Process*, the *Cauer* table of the window holds the Cauer network
equivalent to the Foster network: one resistance `Rth_cauer` (K/W) and one
capacitance `C_cauer` (J/K) per cell, from the junction to the ambient. Click
*Copy* above it, or use *Export All Data* (sheet *Cauer* of the workbook).

The command line writes the same network to `cauer.txt` and to the *Cauer*
sheet of `MEAS_IGBT_results.xlsx`:

```bash
python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx
```

The Cauer table follows the last *Process*. After *Update Foster Model*, it
still shows the network of the identification, not the edited one (see
[Edit the Foster poles by hand](#edit-the-foster-poles-by-hand)).

## Export the network to LTspice

The tool writes the identified network as two LTspice models, one for the
Foster network and one for the Cauer network, with the same pins and
structure as the model of kicad_icepak (v47). Each model comes with its
symbol and its test bench.

**From the window.**

1. Process the data, and edit the poles if needed (click *Update Foster
   Model* after editing).
2. Click *Export LTspice* and choose a folder.
3. The status says
   `LTspice models exported: MEAS_IGBT_FOSTER, MEAS_IGBT_CAUER`. The folder
   now holds:

   | Network | Model | Symbol | Test bench |
   |---|---|---|---|
   | Foster | `MEAS_IGBT_FOSTER.net` | `MEAS_IGBT_FOSTER.asy` | `MEAS_IGBT_FOSTER_testbench.net` |
   | Cauer | `MEAS_IGBT_CAUER.net` | `MEAS_IGBT_CAUER.asy` | `MEAS_IGBT_CAUER_testbench.net` |

**From the command line.** The command line writes the same six files in
the current folder, next to `foster.txt`:

```bash
python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx
```

**Check a model.** Open `MEAS_IGBT_FOSTER_testbench.net` (or
`MEAS_IGBT_CAUER_testbench.net`) in LTspice and run it. It applies a 1 W step
to the model, with an ambient of 25 °C. Plot `V(T)-V(TAMB)`: it is
$Z_{th}(t)$ in K/W, and ends at the sum of the Foster resistances. Set the
time axis to logarithmic to see the short times. The two test benches give
the same curve.

**Use the model in a circuit.**

1. Choose the Foster or the Cauer model. Copy its model and its symbol, for
   example `MEAS_IGBT_CAUER.net` and `MEAS_IGBT_CAUER.asy`, next to your
   schematic, and place the symbol (*Component*, then the folder of the
   schematic). The symbol finds the `.net` file through its `ModelFile`
   attribute, so no `.include` is needed.
2. Drive `P` with a current equal to the losses of the device, 1 A for 1 W,
   for example with a behavioural current source:
   `B1 0 P I=V(drain,source)*I(Rsense)`.
3. Connect `TAMB` to a voltage source equal to the ambient or case
   temperature, in °C.
4. Read `T` as the temperature, in °C. It can drive a temperature-dependent
   model of the device.

The Foster and the Cauer models give the same $Z_{th}(t)$; either can be
used. Only the inner nodes differ: the inner node voltages of the Cauer
model follow the heat path from the junction, those of the Foster model
have no physical meaning. The model is linear: it doesn't follow
the variation of the thermal conductivities with temperature.

## Change a setting of the analysis

Every setting of the analysis is in `thermal_analysis/config.py`: range of M,
factors of the scan of the time constants, settings of PyRth, and the
switches described in [Differences with Zth_to_Foster](differences.md).

1. Open `thermal_analysis/config.py` in a text editor.
2. Change the value. Each one has a comment that says what it does.
3. Start the tool again. The window reads the settings when it processes the
   data, but a value changed while the window is open is only taken into
   account after a restart.

[Settings and switches](reference.md#settings-and-switches) lists every
value.

## Get the results of Zth_to_Foster back

The package corrects four points of the stand-alone Zth_to_Foster tool,
removes the poles below 1e-6 K/W, exports to Excel and also writes the
LTspice models from the command line. To get exactly the results of
Zth_to_Foster, for example to compare with an old analysis, set these
values in `thermal_analysis/config.py`:

```python
FILTER_SMALL_POLES = False
GUI_CONVERT_TO_CAUER = False
GUI_STRUCTURE_FROM_FIRST_TIME = False
GUI_RUN_UNUSED_PYRTH_LASSO = True
DIFFERENTIAL_UNIT_LABEL = "J/K²"
EXCEL_EXPORT = False
CLI_WRITE_LTSPICE = False
```

With these values, the window and the command line give the same tables,
CSV file and PDF text as Zth_to_Foster. Put the values back afterwards.

## Check a fit

After each run:

1. In the *Zth* tab, the dashed Foster curve lies on the measured curve, at
   short times as well as on the plateau. Zoom on the first decades, where
   the curve is small and a misfit is hard to see at full scale.
2. The sum of the Foster resistances equals the last value of $Z_{th}$
   within a few tenths of a percent.
3. No cell sits outside the measured time range: a time constant much
   shorter than the first time point, or much longer than the last one, is
   a fitting artefact.
4. Running the same file twice on the same computer gives the same
   network: nothing in the method is random.

To compare with known results, see [Validation](validation.md).
