"""Regenerate the figures of docs/figures/ that come from the code.

Usage, from anywhere:

    python thermal_analysis/docs/_scripts/make_figures.py

The figures call the real functions of the tool (see _tool.py) on a
synthetic thermal impedance whose Foster network is known: the four-cell
IGBT network of input_data/RECONS_IGBT_*.xlsx. Run this script again after
you change an identification function.

The network diagrams need the schemdraw package (pip install schemdraw).
The screenshots of the GUI come from make_screenshots.py instead.
"""

from __future__ import annotations

import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from _tool import DOCS, identify, load  # noqa: E402

warnings.filterwarnings("ignore")
FIG = DOCS / "figures"
FIG.mkdir(exist_ok=True)

# Reference network: the "Measured" columns of RECONS_IGBT_*.xlsx
R_TRUE = np.array([0.007694, 0.010756, 0.031688, 0.033822])      # K/W
TAU_TRUE = np.array([0.00015, 0.02399, 0.828796, 5.633773])      # s

# Colours: validated categorical slots 1-3, text and grid in neutral inks
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#d9d8d4"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 110, "font.size": 9,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "xtick.color": MUTED, "ytick.color": MUTED,
    "lines.linewidth": 2, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
})


def synthetic(points_per_decade=20, t_min=5e-5, t_max=50.0):
    n = int(np.log10(t_max / t_min) * points_per_decade) + 1
    t = np.logspace(np.log10(t_min), np.log10(t_max), n)
    return t, (R_TRUE[:, None] * (1 - np.exp(-t / TAU_TRUE[:, None]))).sum(0)


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("written", FIG / name)


def fig_networks():
    try:
        import schemdraw
        import schemdraw.elements as elm
    except ImportError:
        print("schemdraw missing: networks.png not regenerated")
        return
    from PIL import Image

    schemdraw.config(fontsize=13, lw=1.4)
    parts = []
    for kind in ("Foster", "Cauer"):
        d = schemdraw.Drawing(show=False)
        d += elm.Label().at((3.5, 4.2)).label(f"{kind} network", fontsize=15)
        src = d.add(elm.SourceI().up(3).label("P", loc="top"))
        d.add(elm.Ground().at(src.start))
        d.add(elm.Line().at(src.end).right(1.5))
        d.add(elm.Dot().label("$T_j$", loc="top"))
        if kind == "Cauer":
            d.add(elm.Line().right(0.75))
        for k in range(1, 4):
            if kind == "Foster":
                start = d.here
                d.add(elm.Resistor().right().label(f"$R_{k}$"))
                end = d.here
                d.add(elm.Line().at(start).down(1.5))
                d.add(elm.Capacitor().right().label(f"$C_{k}$", loc="bottom"))
                d.add(elm.Line().up(1.5))
                d.here = end
            else:
                d.push()
                d.add(elm.Capacitor().down(3).label(f"$C_{k}$", loc="bottom"))
                d.add(elm.Ground())
                d.pop()
                d.add(elm.Resistor().right().label(f"$R_{k}$"))
        d.add(elm.Line().down(3))
        d.add(elm.Ground())
        d += elm.Label().at((d.here[0] + 1.6, d.here[1] + 0.4)).label("ambient")
        png = FIG / f"_tmp_{kind}.png"
        d.save(str(png), dpi=110)
        parts.append(Image.open(png).convert("RGB"))
        png.unlink()
    gap = 60
    height = max(p.height for p in parts)
    out = Image.new("RGB", (sum(p.width for p in parts) + gap, height), "white")
    out.paste(parts[0], (0, height - parts[0].height))
    out.paste(parts[1], (parts[0].width + gap, height - parts[1].height))
    out.save(FIG / "networks.png")
    print("written", FIG / "networks.png")


def fig_nid_steps(ta, t, z, res):
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.5))
    a = ax[0]
    a.semilogx(t, z, color=BLUE, label="input $Z_{th}$ (4-cell network)")
    a.semilogx(t, res["Z_foster"], "--", color=ORANGE, label="identified Foster network")
    a.set(title="1. Thermal impedance", xlabel="time (s)", ylabel="$Z_{th}$ (K/W)")
    a.legend(loc="upper left")
    a = ax[1]
    a.plot(res["z"], res["dZ_dz"], color=BLUE)
    a.set(title="2. Derivative in log time (dZ_dln_t)", xlabel="z = ln t",
          ylabel="dZ$_{th}$/dz (K/W)")
    a = ax[2]
    a.plot(res["z"], res["spectrum"], color=BLUE,
           label=f"R(z), M = {res['M']}")
    for k, tau in enumerate(TAU_TRUE):
        a.axvline(np.log(tau), color=MUTED, ls=":", lw=1.2,
                  label="true time constants" if k == 0 else None)
    a.set(title="3. Time-constant spectrum (my_deconv)", xlabel="z = ln τ",
          ylabel="R(z) (K/W)")
    a.legend(loc="upper left", frameon=True, framealpha=1, edgecolor="none")
    fig.tight_layout()
    save(fig, "nid_steps.png")


def fig_effect_of_m(ta, t, z):
    zz, dz = ta.dZ_dln_t(t, z)
    fig, a = plt.subplots(figsize=(7.5, 3.6))
    for m, col in zip((3, 30, 300), (BLUE, ORANGE, AQUA)):
        a.plot(zz, ta.my_deconv(dz, zz, M=m), color=col, label=f"M = {m}")
    for k, tau in enumerate(TAU_TRUE):
        a.axvline(np.log(tau), color=MUTED, ls=":", lw=1.2,
                  label="true time constants" if k == 0 else None)
    a.set(title="Spectrum after M Richardson-Lucy iterations",
          xlabel="z = ln τ", ylabel="R(z) (K/W)")
    a.legend(loc="upper left")
    save(fig, "effect_of_m.png")


def fig_structure_functions(ta, res):
    r, tau = res["R"], res["tau"]
    rc, cc = ta.foster_to_cauer(r, tau / r)
    rc, cc = ta.cauer_structure_function_max_test(rc, cc)
    r_cum, c_cum = ta.cumulative_structure_function(rc, cc)
    r_cum, c_cum = ta.filter_cumulative_min_resistance(r_cum, c_cum, Rmin=1e-6)
    r_diff, k = ta.differential_structure_function(r_cum, c_cum)
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    a = ax[0]
    a.step(np.r_[0, r_cum], np.r_[c_cum[0], c_cum], where="pre", color=BLUE)
    a.plot(r_cum, c_cum, "o", ms=6, color=BLUE, mec="white", mew=1)
    a.set_yscale("log")
    a.set(title="Cumulative structure function", xlabel="$R_Σ$ (K/W)",
          ylabel="$C_Σ$ (J/K)")
    a = ax[1]
    a.plot(r_diff, k, "o", ms=6, color=BLUE, mec="white", mew=1)
    a.set_yscale("log")
    a.set(title="Differential structure function", xlabel="$R_Σ$ (K/W)",
          ylabel="$dC_Σ/dR_Σ$ (W²s/K²)")
    for a in ax:
        a.axvline(R_TRUE.sum(), color=MUTED, ls=":", lw=1.2)
        a.text(R_TRUE.sum(), a.get_ylim()[0], " total $R_{th}$", color=MUTED,
               va="bottom", ha="left", fontsize=8)
    fig.tight_layout()
    save(fig, "structure_functions.png")


def main():
    ta, name = load()
    print("code:", name)
    fig_networks()
    t, z = synthetic()
    res = identify(ta, t, z)
    print("identified M =", res["M"], "R =", res["R"], "tau =", res["tau"])
    fig_nid_steps(ta, t, z, res)
    fig_effect_of_m(ta, t, z)
    fig_structure_functions(ta, res)


if __name__ == "__main__":
    main()
