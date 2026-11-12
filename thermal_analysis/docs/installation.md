# Installation

## Install and start the tool

Put the `thermal_analysis` folder in your project, then, from the folder
that contains it:

```bash
pip install -r thermal_analysis/requirements.txt
python -m thermal_analysis
```

The window *Thermal Impedance Analysis tool* opens. With a `-file`
argument, the same command runs the command line instead, without a window.

The command depends on the current folder, the one shown before the prompt
(`PS C:\Users\...\Downloads>` in PowerShell):

| Current folder | Window | Command line |
|---|---|---|
| the folder that contains `thermal_analysis` | `python -m thermal_analysis` | `python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx` |
| the `thermal_analysis` folder itself | `python __main__.py` | `python __main__.py -file input_data/MEAS_IGBT.xlsx` |
| any other folder | `python <path>/thermal_analysis/__main__.py` | `python <path>/thermal_analysis/__main__.py -file <path>/MEAS_IGBT.xlsx` |

`python -m thermal_analysis` only works from the folder that contains
`thermal_analysis`: from inside it, Python answers
`No module named 'thermal_analysis'`. Running `__main__.py` works from
anywhere, also with *Run Python File* in VS Code. Every command starts with
`python`, and a file path that contains spaces goes between quotes.

`-nfb 8` sets the maximum number of Foster branches; it is optional:

```bash
python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx -nfb 8
```

## Requirements

- Python 3 with tkinter, for the window. The tool was tested with
  Python 3.12 (window and command line) and 3.13 (command line). tkinter
  comes with the python.org installers for Windows and macOS; on Debian or
  Ubuntu, install the `python3-tk` package.
- NumPy older than 2.0 for the window, because PyRth requires it.
  `requirements.txt` pins it. The command line alone also runs with
  NumPy 2.
- Windows, Linux or macOS. Nothing in the tool depends on the operating
  system.

## What each Python package does

| Package | Used for | Needed by |
|---|---|---|
| `numpy`, `scipy` | numerical work, Savitzky-Golay filter, least-squares fits | window, command line |
| `numba`, `joblib` | imported by the computation modules; `joblib` runs the search over M on several threads | window, command line |
| `pandas`, `openpyxl` | reading `.xlsx` and `.csv` files, Excel and CSV exports | window, command line |
| `matplotlib` | plots and PDF report | window |
| `pillow` | pictures of the *Notice* tab | window |
| `PyRth` | structure functions shown in the window (see [In the window](method.md#in-the-window)) | window |

`import thermal_analysis` loads only the computation modules. The window
(`thermal_analysis.gui`) imports tkinter, Matplotlib, Pillow and PyRth when it
starts, so the command line also runs on a server without a display.

## Check the installation

1. Run `python -m thermal_analysis`. The window opens with an empty plot.

   If a package is missing, Python stops before the window opens and names
   it: `ModuleNotFoundError: No module named 'PyRth'`, for example. Install
   it with `pip install`.

2. Click *Load File*, choose `thermal_analysis/input_data/MEAS_IGBT.xlsx`,
   then click *Process*. After 10 to 30 s, depending on the computer, the
   status line at the bottom left says `Processed successfully` and the *Zth*
   tab shows the measured curve with the Foster curve on top of it.

3. To check the command line, run:

   ```bash
   python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx
   ```

   It prints its progress and writes in the current folder `foster.txt`,
   `cauer.txt`, `cumul.txt`, `diff.txt`, five `*_plot.txt` files, the Excel
   workbook `MEAS_IGBT_results.xlsx` and six LTspice files. `foster.txt`
   holds 7 lines of values.
