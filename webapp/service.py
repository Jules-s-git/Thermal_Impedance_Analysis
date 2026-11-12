"""Reading, analysis and export used by the web page.

The analysis itself is ``thermal_analysis.analyse``, with the structure
functions of the command line (``structure="cauer"``): the web version needs
neither PyRth nor tkinter. This module only checks the input file and
packs the results.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# thermal_analysis/ sits in the folder above webapp/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thermal_analysis import analyse  # noqa: E402
from thermal_analysis import config  # noqa: E402
from thermal_analysis.data_io import export_excel, write_cli_outputs  # noqa: E402
from thermal_analysis.ltspice import base_name, write_ltspice  # noqa: E402

MIN_POINTS = 20


class InputError(ValueError):
    """The file can't be used as a Zth(t) curve. The message is shown to the user."""


def load_table(source, filename: str) -> tuple[np.ndarray, np.ndarray]:
    """Read time and Zth from an .xlsx, .csv or text file.

    Same rule as ``thermal_analysis.data_io.read_table``: columns named
    ``time`` and ``Zth`` if they exist, otherwise the first two columns.
    Points with ``time <= 0`` are dropped. ``source`` is a path or a
    file-like object. Unlike ``read_table``, bad files give a clear message.
    """
    name = filename.lower()
    try:
        if name.endswith(".xlsx"):
            df = pd.read_excel(source)
        elif name.endswith(".csv"):
            df = pd.read_csv(source, sep=None, engine="python")
        elif name.endswith((".txt", ".dat")):
            df = pd.read_csv(source, sep=None, engine="python", comment="#", header=None)
        else:
            raise InputError("Use an .xlsx, .csv or .txt file.")
    except InputError:
        raise
    except Exception as exc:  # unreadable file
        raise InputError(f"The file can't be read: {exc}") from exc

    if df.shape[1] < 2:
        raise InputError("The file needs two columns: time (s) and Zth (K/W).")
    if "time" in df.columns and "Zth" in df.columns:
        t_raw, z_raw = df["time"], df["Zth"]
    else:
        t_raw, z_raw = df.iloc[:, 0], df.iloc[:, 1]

    t = pd.to_numeric(t_raw, errors="coerce").to_numpy(dtype=float)
    z = pd.to_numeric(z_raw, errors="coerce").to_numpy(dtype=float)
    keep = np.isfinite(t) & np.isfinite(z) & (t > 0)
    t, z = t[keep], z[keep]
    if t.size < MIN_POINTS:
        raise InputError(
            f"Only {t.size} usable points (time > 0 and numeric). At least {MIN_POINTS} are needed."
        )
    order = np.argsort(t)
    t, z = t[order], z[order]
    if np.any(np.diff(t) <= 0):
        raise InputError("The time column has repeated values.")
    return t, z


def run(time, Z_meas, n_branches: int = 10):
    """Analysis of one curve, as the command line does it."""
    try:
        res = analyse(time, Z_meas, n_branches=n_branches, structure="cauer", spectra=True)
    except (TypeError, ValueError, IndexError, np.linalg.LinAlgError) as exc:
        raise InputError(
            "No Foster network was found. Check that the curve is a Zth(t) step "
            f"response ({type(exc).__name__}: {exc})."
        ) from exc
    if res.Rth_foster is None or len(res.Rth_foster) == 0:
        raise InputError("The fit gave no Foster cell. Check that the curve is a Zth(t) step response.")
    return res


def max_deviation_percent(res) -> float:
    """Largest gap between the Foster curve and the data, in % of the largest Zth."""
    scale = float(np.max(np.abs(res.Z_meas)))
    return 100.0 * float(np.max(np.abs(res.Z_foster - res.Z_meas))) / scale


def results_zip(res, filename: str) -> bytes:
    """The four tables, the Excel workbook and the LTspice models, as one zip.

    Same files as the command line (``python -m thermal_analysis -file ...``).
    """
    base = base_name(filename)
    buf = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        write_cli_outputs(res, tmp)
        for name in ("foster.txt", "cauer.txt", "cumul.txt", "diff.txt"):
            zf.write(os.path.join(tmp, name), name)
        workbook = os.path.join(tmp, f"{base}_results.xlsx")
        export_excel(res, workbook, diff_unit=config.DIFFERENTIAL_UNIT_LABEL, source=filename)
        zf.write(workbook, os.path.basename(workbook))
        try:
            model = write_ltspice(res.Rth_foster, res.tau_foster, tmp,
                                  t_end=res.time[-1], source=filename)
        except ValueError:
            model = None
        if model is not None:
            for path in model.files:
                zf.write(path, os.path.basename(path))
    return buf.getvalue()
