"""Reproduce the tables of docs/validation.md.

Usage, from anywhere (the last table needs PyRth):

    python thermal_analysis/docs/_scripts/validate.py          # about 7 minutes
    python thermal_analysis/docs/_scripts/validate.py --quick  # skips the 535-point LTspice file

Each run calls pipeline.analyse with the settings of config.py on the files
of input_data/, and prints Markdown tables. Copy the tables into
docs/validation.md when the results change.
"""

from __future__ import annotations

import sys
import time
import warnings

import numpy as np
import pandas as pd

from _tool import data_dir, identify, load

warnings.filterwarnings("ignore")

R_TRUE = np.array([0.007694, 0.010756, 0.031688, 0.033822])
TAU_TRUE = np.array([0.00015, 0.02399, 0.828796, 5.633773])


def read(path):
    df = pd.read_excel(path)
    t = df.iloc[:, 0].to_numpy(float)
    z = df.iloc[:, 1].to_numpy(float)
    keep = np.isfinite(t) & np.isfinite(z) & (t > 0)
    return t[keep], z[keep]


def resample_log(t, z, per_decade=20):
    n = int(np.ceil(np.log10(t[-1] / t[0]) * per_decade)) + 1
    t_log = np.logspace(np.log10(t[0]), np.log10(t[-1]), n)
    return t_log, np.interp(np.log(t_log), np.log(t), z)


def run(ta, t, z):
    start = time.time()
    res = identify(ta, t, z)
    res["seconds"] = time.time() - start
    order = np.argsort(res["tau"])
    res["R"], res["tau"] = res["R"][order], res["tau"][order]
    err = ta.reconstruct_foster(t, res["R"], res["tau"]) - z
    res["rel_rmse"] = np.sqrt(np.mean(err ** 2)) / np.ptp(z)
    res["max_err"] = np.max(np.abs(err)) / z[-1]
    return res


def known_network(ta, quick):
    print("\n### Four-cell IGBT network (known values)\n")
    print("| File | Points | Poles | Largest error on R | Largest error on τ | Time (s) |")
    print("|---|---|---|---|---|---|")
    files = sorted(data_dir().glob("RECONS_IGBT_*PTS.xlsx"),
                   key=lambda p: int(p.stem.split("_")[-1][:-3]))
    cases = [(f.name, *read(f)) for f in files]
    t, z = read(data_dir() / "LTSPICE_IGBT.xlsx")
    if not quick:
        cases.append(("LTSPICE_IGBT.xlsx", t, z))
    cases.append(("LTSPICE_IGBT.xlsx, resampled 20/decade", *resample_log(t, z)))
    for name, t, z in cases:
        res = run(ta, t, z)
        if len(res["R"]) == len(R_TRUE):
            er = np.max(np.abs(res["R"] / R_TRUE - 1))
            et = np.max(np.abs(res["tau"] / TAU_TRUE - 1))
            errs = f"{100 * er:.2f} % | {100 * et:.2f} %"
        else:
            errs = "n/a | n/a"
        print(f"| `{name}` | {len(t)} | {len(res['R'])} | {errs} | {res['seconds']:.0f} |")


def other_files(ta, pattern, title):
    print(f"\n### {title}\n")
    print("| File | Points | Time span (s) | Poles after deconvolution | Final poles "
          "| Sum of R / Zth(end) | Relative RMSE | Largest error / Zth(end) | Time (s) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for f in sorted(data_dir().glob(pattern)):
        t, z = read(f)
        res = run(ta, t, z)
        print(f"| `{f.name}` | {len(t)} | {t[0]:.2g} to {t[-1]:.3g} | "
              f"{len(res['R_deconv'])} | {len(res['R'])} | {res['R'].sum() / z[-1]:.4f} | "
              f"{100 * res['rel_rmse']:.2f} % | {100 * res['max_err']:.2f} % | "
              f"{res['seconds']:.0f} |")


def foster_to_cauer_round_trip(ta):
    print("\n### Foster to Cauer conversion\n")
    print("| Poles | Spread of τ | Non-positive elements | Largest error on Z(jω) / Rth |")
    print("|---|---|---|---|")
    rng = np.random.default_rng(0)
    for n, decades in ((4, 5), (10, 8), (20, 10), (40, 12), (100, 14)):
        tau = np.logspace(-6, -6 + decades, n)
        r = rng.uniform(0.01, 1.5, n)
        rc, cc = ta.foster_to_cauer(r, tau / r)
        s = 1j * np.logspace(-3, 3, 300) / np.sqrt(tau[0] * tau[-1])
        zf = sum(ri / (1 + ti * s) for ri, ti in zip(r, tau))
        # Cauer ladder seen from the input: C1 to ground, R1, C2, ..., Rn to ground
        zc = np.zeros_like(s)
        for k in range(len(cc) - 1, -1, -1):
            zc = zc + rc[k]
            zc = 1 / (s * cc[k] + 1 / zc)
        bad = int(np.sum(np.asarray(rc) <= 0) + np.sum(np.asarray(cc) <= 0))
        err = np.max(np.abs(zc - zf)) / r.sum()
        print(f"| {n} | 1e{decades} | {bad} | {err:.1e} |")


def window_structure(ta):
    print("\n### Structure functions of the window\n")
    print("| File | Sum of R (K/W) | Last RΣ, GUI_STRUCTURE_FROM_FIRST_TIME = True | Last RΣ, False |")
    print("|---|---|---|---|")
    saved = ta.config.GUI_STRUCTURE_FROM_FIRST_TIME
    for f in sorted(data_dir().glob("MEAS_*.xlsx")):
        t, z = read(f)
        last = {}
        for flag in (True, False):
            ta.config.GUI_STRUCTURE_FROM_FIRST_TIME = flag
            res = ta.analyse(t, z, structure="pyrth", spectra=False)
            last[flag] = float(np.max(res.Rth_cum))
        print(f"| `{f.name}` | {res.Rth_foster.sum():.4f} | {last[True]:.4f} | {last[False]:.4f} |")
    ta.config.GUI_STRUCTURE_FROM_FIRST_TIME = saved


def main():
    ta, name = load()
    print(f"Code: {name}; NumPy {np.__version__}")
    quick = "--quick" in sys.argv
    known_network(ta, quick)
    other_files(ta, "LTSPICE_MOD*.xlsx", "LTspice networks with 1, 3 and 5 cells")
    other_files(ta, "MEAS_*.xlsx", "Measured thermal impedances")
    foster_to_cauer_round_trip(ta)
    try:
        import PyRth  # noqa: F401
    except ImportError:
        print("\nPyRth not installed: structure functions of the window skipped")
    else:
        window_structure(ta)


if __name__ == "__main__":
    main()
