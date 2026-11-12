# -*- coding: utf-8 -*-
"""Command line of the thermal impedance analysis.

    python -m thermal_analysis.cli -file input.xlsx -nfb 10    (-nfb is optional)

Same options and outputs as cli_main.py of the stand-alone Zth_to_Foster
tool: foster.txt, cauer.txt, cumul.txt, diff.txt and five *_plot.txt
scripts, written in the current folder. With config.CLI_WRITE_LTSPICE (the
default), also the LTspice models of the network: for the Foster and the
Cauer network, a model <NAME>_<KIND>.net, a symbol <NAME>_<KIND>.asy and a
test bench <NAME>_<KIND>_testbench.net, where <NAME> comes from the name of
the input file. With config.EXCEL_EXPORT (the default), also the Excel
workbook <NAME>_results.xlsx.
"""

from __future__ import annotations

if not __package__:  # run as a file (python thermal_analysis/cli.py): start it as a module
    import os as _os, runpy as _runpy, sys as _sys
    _pkg_dir = _os.path.dirname(_os.path.abspath(__file__))
    _sys.path.insert(0, _os.path.dirname(_pkg_dir))
    _runpy.run_module(_os.path.basename(_pkg_dir) + ".cli", run_name="__main__")
    raise SystemExit

import argparse
import os
import sys

from . import config
from .data_io import export_excel, read_table, write_cli_outputs
from .ltspice import base_name, write_ltspice
from .pipeline import analyse


def _prog():
    """The command as the user typed it, for the usage line."""
    spec = getattr(sys.modules.get("__main__"), "__spec__", None)
    if spec is not None:  # python -m thermal_analysis[.cli]
        return "python -m " + spec.name.replace(".__main__", "")
    return "python " + (sys.argv[0] or "__main__.py")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=_prog(), description="Thermal Impedance Analysis tool (command line)",
        epilog="example: -file input_data/MEAS_IGBT.xlsx -nfb 8   "
               "(write -nfb 8, without brackets; -nfb is optional)")
    parser.add_argument("-file", "--datafile", required=True, metavar="FILE",
                        help="input file: time (s) and Zth (K/W), .xlsx, .csv or text")
    parser.add_argument("-nfb", "--n_foster_branches", type=int, metavar="N",
                        default=config.DEFAULT_MAX_BRANCHES,
                        help=f"maximum number of Foster branches (default {config.DEFAULT_MAX_BRANCHES})")
    args, extra = parser.parse_known_args(argv)
    if extra:
        if any(a.startswith("[") or a.endswith("]") for a in extra):
            parser.error("unrecognized arguments: " + " ".join(extra) + ". The brackets of "
                         "[-nfb N] only mark an optional argument: type -nfb 8, or nothing")
        parser.error("unrecognized arguments: " + " ".join(extra) + ". Put a file path "
                     "that contains spaces between quotes")
    if not os.path.isfile(args.datafile):
        parser.error(f"file not found: {args.datafile} (current folder: {os.getcwd()})")
    return args


def main(argv=None):
    args = parse_args(argv)
    time, z_meas = read_table(args.datafile)
    result = analyse(time, z_meas, args.n_foster_branches, structure="cauer", spectra=False)
    write_cli_outputs(result, ".")
    if config.EXCEL_EXPORT:  # switch N2
        workbook = f"{base_name(args.datafile)}_results.xlsx"
        export_excel(result, workbook, diff_unit=config.DIFFERENTIAL_UNIT_LABEL,
                     source=args.datafile)
        print("Excel workbook: " + workbook)
    if config.CLI_WRITE_LTSPICE:  # switch N1
        model = write_ltspice(result.Rth_foster, result.tau_foster, ".",
                              t_end=result.time[-1], source=args.datafile)
        print("LTspice models: " + ", ".join(os.path.basename(f) for f in model.files))
        for note in model.notes:
            print(note)
    return result


if __name__ == "__main__":
    main()
