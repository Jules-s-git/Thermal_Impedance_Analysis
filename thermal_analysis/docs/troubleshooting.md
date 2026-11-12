# Troubleshooting

Each problem below has its own heading, so you can link to it directly. In
the window, an error opens a dialog with the Python message, without the
name of the error type; some errors only show in the console that started
the window. The command line prints the full Python traceback.

## Start-up

### ModuleNotFoundError: No module named ...

A package is missing: `PyRth`, `numba`, `joblib`, `PIL` (package `pillow`)
or `tkinter`. Python stops before the window opens.

Install the packages with `pip install -r thermal_analysis/requirements.txt` (see
[Installation](installation.md)). `tkinter` doesn't install with pip: on
Debian or Ubuntu, install `python3-tk`; on Windows and macOS, use a
python.org installer. The command line needs neither `tkinter` nor `PyRth`.

### No module named thermal_analysis

Message: `No module named thermal_analysis` or
`Error while finding module specification for 'thermal_analysis.cli'`, after
`python -m thermal_analysis` or `python -m thermal_analysis.cli`.

Python looks for the package in the current folder, so `-m` only works from
the folder that *contains* `thermal_analysis`. From inside the
`thermal_analysis` folder, run the file instead:

```bash
python __main__.py -file input_data/MEAS_IGBT.xlsx
```

`python <path>/thermal_analysis/__main__.py` works from any folder. See
[Install and start the tool](installation.md#install-and-start-the-tool)
for the command to use in each folder.

### unrecognized arguments: [-nfb N]

The usage line `[-h] -file FILE [-nfb N]` uses brackets to mark the optional
arguments. Type the argument without brackets, with a number, or leave it
out:

```bash
python __main__.py -file input_data/MEAS_IGBT.xlsx -nfb 8
python __main__.py -file input_data/MEAS_IGBT.xlsx
```

Any other unrecognized argument is often the end of a file path that
contains spaces: put the path between quotes.

### error: file not found

The command line doesn't find the input file. The message gives the current
folder: a relative path such as `input_data/MEAS_IGBT.xlsx` starts from it.
Check the name and the extension (`MEAS_IGBT.xlsx`, not `MEAS_IG`), or give
the full path.

### The term '-m' is not recognized

PowerShell message, when the command starts with `-m`: the word `python` is
missing. Type `python -m thermal_analysis ...`.

### ImportError: attempted relative import with no known parent package

A module of the package was run as a file, for example `pipeline.py` with
*Run Python File* in VS Code. The modules import each other as parts of the
package, so they can't run alone. Run `thermal_analysis/__main__.py`
instead (window, or command line with arguments), or
`thermal_analysis/cli.py`. These two files, and `gui/app.py`, can run as
files.

## Loading data

### single positional indexer is out-of-bounds

The file has only one column as read by the tool. Usual cause: a `.csv` file
saved with semicolons, as Excel does with French or German settings. The
tool reads `.csv` files with commas only.

Save the file as `.xlsx` instead, or replace the semicolons by commas and the
decimal commas by points.

### The first point is missing

The tool reads the first line as a header, in the data box and in `.xlsx`
and `.csv` files. If your data has no header line, the first point becomes
the header. Add a header line, such as `time` and `Zth`.

### ValueError: could not convert string 'time' to float64

Command line only, with a file that is neither `.xlsx` nor `.csv`. The
command line reads other files as plain numbers, without a header line.
Remove the header line, start it with `#`, or save the file as `.csv` or
`.xlsx`.

## Processing

### IndexError: too many indices for array

Dialog message: `too many indices for array: array is 1-dimensional, but 2
were indexed`, after *Process*.

The data box holds no usable line. Causes:

- the box is empty, or holds only the header line;
- the columns are separated by commas or semicolons, for example text
  pasted from a `.csv` file. The window splits lines on spaces and tabs
  only.

Load the file with *Load File*, or paste from a spreadsheet (see
[Paste data from a spreadsheet](howto.md#paste-data-from-a-spreadsheet)).

### invalid literal for int() with base 10

The *Maximum number of Foster branches* field doesn't hold a whole number.
Enter an integer such as 10.

### The window doesn't respond

During *Process*, the window doesn't respond to clicks until the
computation ends: 10 to 30 s for 126 points, depending on the computer.
This is normal. With several
hundred points, it can take minutes; see
[Processing takes minutes](#processing-takes-minutes).

### Processing takes minutes

The computation time grows with the square of the number of points: 3 s for
50 points, 27 s for 500 points spaced in log time, 141 s for 535 points from
LTspice. Resample the curve to 20 points per decade (see
[Resample a long or linear curve](howto.md#resample-a-long-or-linear-curve)).

### The Foster curve misses the start or the end of the curve

- At short times: the first points may lie before the fastest time constant
  the data can resolve, or the sampling is too coarse there. Check that the
  data has several points per decade at short times.
- At long times: if the curve doesn't end on a plateau, the slowest part of
  the system hasn't settled, and the tool can't know its resistance. Measure
  or simulate longer.
- Everywhere: raise the maximum number of branches (see
  [Choose the maximum number of Foster branches](howto.md#choose-the-maximum-number-of-foster-branches)).

### More Foster cells than the maximum

When the deconvolution finds more cells than the maximum, the tool keeps
them all and skips the least-squares step. This happens on noisy data, where
the spectrum has many small peaks. The fit is then usually poorer. Smooth or
resample the data, or edit the cells by hand (see
[Edit the Foster poles by hand](howto.md#edit-the-foster-poles-by-hand)).

## Results

### Repeated or missing values in the exported CSV file

The CSV file of *Export All Data* and *Copy All Data* give every column the
length of the time column. Shorter columns repeat their last value; longer columns, such
as the structure functions on a file with fewer than about 200 points, are
cut. See [Export the results](howto.md#export-the-results). The Excel
workbook, the default format of *Export All Data*, keeps each table at its
own length.

### Export does nothing

Before the first *Process*, *Export All Data* and *Copy All Data* fail with
an error in the console only (`'ThermalGUI' object has no attribute
'time'`), and *Export PDF* shows it in a dialog. Click *Process* first.

### The edited Foster network isn't in the Cauer table

*Update Foster Model* only rebuilds the Foster curve. The tables on the
right, the structure functions and the spectrum keep the results of the last
*Process*. See [Edit the Foster poles by hand](howto.md#edit-the-foster-poles-by-hand).

### spectrum_plot.txt shows the derivative

The `spectrum_plot.txt` file of the command line plots
$dZ_{th}/d\ln t$ against time, despite its title *Spectrum R*. The command
line doesn't write the spectrum. To plot it, use the window.

### The command line overwrote my results

The command line always writes the same nine text files (`foster.txt`,
`cauer.txt`, …) in the current folder; only the LTspice files carry the name
of the input file. Run each file from its own folder.

## LTspice models

### Process data first: there is no Foster network to export

*Export LTspice* was clicked before *Process*, or every cell of the Foster
table has a resistance or a time constant of 0. Process the data, or fix the
table and click *Update Foster Model*, then export again.

### Cauer model not written

The Foster to Cauer conversion gave a resistance or a capacitance that isn't
positive, which can happen through rounding on networks whose time
constants are very close or span many decades. Only the three Foster files
are written; the Foster model gives the same $Z_{th}(t)$. To check the network, see
[Foster to Cauer conversion](validation.md#foster-to-cauer-conversion).

### LTspice: Unknown subcircuit

LTspice doesn't find the model, `<NAME>_FOSTER.net` or `<NAME>_CAUER.net`.
The symbol looks for it through its
`ModelFile` attribute, by name, in the folder of the schematic and in the
LTspice library folders. Copy the `.net` file next to the schematic, or
right-click the symbol and write the full path of the file in `ModelFile`.

### LTspice: Time step too small

The test bench uses a step that rises in 0.1 µs to 1 µs. If a circuit around
the model makes the simulation stop with *Time step too small*, give the
power source a slower rise, for example `PWL(0 0 10u 1)`: the model only
loses the times shorter than about 10 times the rise time.
