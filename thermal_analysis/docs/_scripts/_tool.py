"""Import the thermal_analysis package for the documentation scripts.

The documentation lives in thermal_analysis/docs/. The scripts add the
folder above the package to the Python path and import the package under
its folder name, so they work wherever the folder is.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
PACKAGE_DIR = DOCS.parent


def load():
    """Return (package, name)."""
    sys.path.insert(0, str(PACKAGE_DIR.parent))
    name = PACKAGE_DIR.name
    return importlib.import_module(name), name


def identify(ta, time, z_meas, max_poles=10):
    """Run pipeline.analyse as the command line does, plus the spectra.

    Returns a dict with the intermediate results used by the figures and
    the validation tables.
    """
    import numpy as np

    res = ta.analyse(time, z_meas, max_poles, structure="cauer", spectra=True)
    return {
        "R_deconv": res.Rth_deconv, "z": res.z, "dZ_dz": res.dZ_dz, "M": res.M_opt,
        "R": np.asarray(res.Rth_foster), "tau": np.asarray(res.tau_foster),
        "Z_foster": res.Z_foster, "spectrum": res.R_spec, "result": res,
    }


def data_dir() -> Path:
    """Folder with the sample files."""
    return PACKAGE_DIR / "input_data"
