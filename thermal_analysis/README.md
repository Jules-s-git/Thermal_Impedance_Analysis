# thermal_analysis

Thermal impedance analysis: $Z_{th}(t)$ to Foster network, Cauer network and
structure functions. The package holds the whole Thermal Impedance Analysis
tool (window and command line), not only its functions.

## Start the tool

From the folder that contains `thermal_analysis/` (the project root):

```bash
python -m thermal_analysis                                                   # window
python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx  # command line
python -m thermal_analysis -file thermal_analysis/input_data/MEAS_IGBT.xlsx -nfb 8
python -m thermal_analysis.cli -h                                            # options
```

From inside the `thermal_analysis/` folder, `-m` doesn't work; run the file:

```bash
python __main__.py                                   # window
python __main__.py -file input_data/MEAS_IGBT.xlsx   # command line
```

Running the file also works from any other folder, for example with
*Run Python File* in VS Code: `python <path>/thermal_analysis/__main__.py`.
`-nfb` is optional: type `-nfb 8`, without the brackets of the usage line.

From Python:

```python
from thermal_analysis import analyse
from thermal_analysis.data_io import read_table

time, zth = read_table("input_data/MEAS_IGBT.xlsx")
result = analyse(time, zth, n_branches=10, structure="cauer")
print(result.Rth_foster, result.tau_foster, result.Rth_cauer, result.C_cauer)
```

`structure="pyrth"` computes the structure functions as the window does
(needs PyRth); `structure="cauer"` as the command line does.

The LTspice models of a network (the files of *Export LTspice*):

```python
from thermal_analysis.ltspice import write_ltspice

write_ltspice(result.Rth_foster, result.tau_foster, "ltspice",
              t_end=result.time[-1], source="MEAS_IGBT.xlsx")
```

## Modules

```text
thermal_analysis/
├── __init__.py            re-exports the functions, analyse and config
├── __main__.py            python -m thermal_analysis: window, or command line with arguments
├── config.py              every setting, and the switches of docs/differences.md
├── pipeline.py            analyse(): the complete analysis, shared by the window and the CLI
├── data_io.py             reading curves, Excel/CSV/PDF/text outputs
├── ltspice.py             LTspice models: Foster and Cauer, each with symbol and test bench
├── cli.py                 command line
├── gui/                   window, one module per part
│   ├── common.py          imports, paths, colours
│   ├── app.py             ThermalGUI: window shell, assembles the mixins
│   ├── step_input.py      InputMixin: data box, Load File, Process, status
│   ├── step_plots.py      PlotsMixin: plot tabs, Notice tab
│   └── step_results.py    ResultsMixin: Foster editor, result tables, copy, export
├── assets/                pictures of the Notice tab
├── references.py          bibliography of the docstrings
├── input_data/            sample curves: measurements and networks with known values
├── docs/                  documentation (Markdown, and the same pages as one PDF)
├── requirements.txt       Python packages
├── deconvolution.py       my_deconv (Richardson-Lucy)
├── foster.py              reconstruct_foster, generate_foster_signal
├── optimization.py        choice of M, scan of tau, least squares
├── cauer.py               foster_to_cauer
├── structure_functions.py cumulative and differential structure functions
└── utils.py               dZ_dln_t, detect_min_max, filters, pad
```

`import thermal_analysis` only loads the computation modules: the window
(`gui`) needs tkinter, Pillow and PyRth and is imported only when it starts.

## Documentation

Start with [docs/README.md](docs/README.md): installation, tutorial, how-to
guides, method, validation, reference and troubleshooting. The same pages
as one PDF: `docs/Thermal_Impedance_Analysis_tool.pdf`.

`config.py` holds every setting, and one switch per difference with the
stand-alone Zth_to_Foster tool (see [docs/differences.md](docs/differences.md)).
