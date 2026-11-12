# -*- coding: utf-8 -*-
"""LTspice model of the identified network.

Writes, for one thermal impedance curve, a model, a symbol and a test bench
for each of the two networks, as kicad_icepak (v47) does for the coupled
model of a board:

    <BASE>_FOSTER.net             subcircuit <BASE>_FOSTER (Foster network)
    <BASE>_FOSTER.asy             LTspice symbol of <BASE>_FOSTER
    <BASE>_FOSTER_testbench.net   power step on <BASE>_FOSTER
    <BASE>_CAUER.net              subcircuit <BASE>_CAUER (Cauer network)
    <BASE>_CAUER.asy              LTspice symbol of <BASE>_CAUER
    <BASE>_CAUER_testbench.net    power step on <BASE>_CAUER

Electrical analogy: 1 A = 1 W, 1 V = 1 degC (or 1 K of rise), 1 Ohm = 1 K/W,
1 F = 1 J/K.

Each subcircuit has the pins of the v47 model, ``P T TAMB``:

* ``P``: power input. The current that enters ``P`` is the dissipated power.
  A 0 V source to ``TAMB`` measures it.
* a current-controlled current source (``F``) copies that current into the
  RC network, whose inner nodes connect to nothing outside the subcircuit;
* ``T``: temperature output, ``V(T) = V(TAMB) + Zth * P``, given by a
  voltage-controlled voltage source (``E``), so a load on ``T`` doesn't
  change the network.

The files only contain ASCII characters, so that every LTspice version reads
them.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import numpy as np

from . import config
from .cauer import foster_to_cauer

__all__ = ["LTspiceModel", "base_name", "cauer_cells", "write_ltspice"]

FMT = "{:.9g}"


@dataclass
class LTspiceModel:
    """Paths of the written files, and what the models contain.

    ``models``, ``symbols`` and ``testbenches`` map ``"FOSTER"`` and
    ``"CAUER"`` to the paths of the files of each network. ``"CAUER"`` is
    missing when the conversion failed (see ``notes``).
    """

    base: str
    models: dict = field(default_factory=dict)
    symbols: dict = field(default_factory=dict)
    testbenches: dict = field(default_factory=dict)
    foster_cells: int = 0
    cauer_cells: int = 0
    notes: list = field(default_factory=list)

    @property
    def names(self):
        """Names of the written subcircuits."""
        return [f"{self.base}_{kind}" for kind in self.models]

    @property
    def files(self):
        return [path for kind in self.models
                for path in (self.models[kind], self.symbols[kind], self.testbenches[kind])]


def base_name(source=None):
    """Name of the model, from the name of the input file.

    ``input_data/MEAS_IGBT.xlsx`` gives ``MEAS_IGBT``. Characters other than
    letters, digits and ``_`` become ``_``; the name is in upper case, as
    in the v47 model, and starts with a letter.
    """
    stem = os.path.splitext(os.path.basename(str(source or "")))[0]
    name = re.sub(r"[^A-Za-z0-9_]", "_", stem).strip("_").upper()
    if not name:
        return config.LTSPICE_DEFAULT_NAME
    if not name[0].isalpha():
        name = "ZTH_" + name
    return name


def _foster_cells(Rth, tau):
    """Foster cells with R > 0 and tau > 0, fastest first."""
    R = np.asarray(Rth, dtype=float).ravel()
    t = np.asarray(tau, dtype=float).ravel()
    if R.size != t.size:
        raise ValueError("Rth_foster and tau_foster have different lengths")
    keep = np.isfinite(R) & np.isfinite(t) & (R > 0) & (t > 0)
    order = np.argsort(t[keep])
    return R[keep][order], t[keep][order]


def cauer_cells(Rth, tau):
    """Cauer ladder equivalent to the Foster network (R_k, tau_k).

    Returns ``(R, C)``, from the junction side, or ``None`` when the
    conversion gives an element that is not positive and finite (rounding
    on networks whose time constants span many decades).
    """
    R, t = _foster_cells(Rth, tau)
    if R.size == 0:
        return None
    rc, cc = foster_to_cauer(R, t / R)
    rc, cc = np.real(np.asarray(rc, dtype=complex)), np.real(np.asarray(cc, dtype=complex))
    if rc.size != R.size or cc.size != R.size:
        return None
    if not (np.all(np.isfinite(rc)) and np.all(np.isfinite(cc))
            and np.all(rc > 0) and np.all(cc > 0)):
        return None
    return rc, cc


# ------------------------------------------------------------------ netlist
def _foster_subckt(name, R, t):
    C = t / R
    lines = [f"* Foster network: {len(R)} cells, Rth = {FMT.format(R.sum())} K/W",
             "*   cell    R (K/W)           C (J/K)           tau (s)",
             *[f"*   {k:<6d}  {FMT.format(r):<16s}  {FMT.format(c):<16s}  {FMT.format(tk)}"
               for k, (r, c, tk) in enumerate(zip(R, C, t), start=1)],
             f".SUBCKT {name} P T TAMB",
             "VSENSE P TAMB 0",
             "F1 TAMB N1 VSENSE 1"]
    # R_k parallel C_k between N_k and N_(k+1); the last cell ends at TAMB
    nodes = [f"N{k}" for k in range(1, len(R) + 1)] + ["TAMB"]
    for k, (r, c) in enumerate(zip(R, C), start=1):
        lines.append(f"R{k} {nodes[k - 1]} {nodes[k]} {FMT.format(r)}")
        lines.append(f"C{k} {nodes[k - 1]} {nodes[k]} {FMT.format(c)}")
    lines += ["E1 T TAMB N1 TAMB 1", f".ENDS {name}"]
    return lines


def _cauer_subckt(name, rc, cc):
    lines = [f"* Cauer network: {len(rc)} cells, Rth = {FMT.format(rc.sum())} K/W",
             "*   cell    R (K/W)           C (J/K)",
             *[f"*   {k:<6d}  {FMT.format(r):<16s}  {FMT.format(c)}"
               for k, (r, c) in enumerate(zip(rc, cc), start=1)],
             f".SUBCKT {name} P T TAMB",
             "VSENSE P TAMB 0",
             "F1 TAMB N1 VSENSE 1"]
    # C_k from N_k to TAMB, R_k from N_k to N_(k+1); the last R ends at TAMB
    nodes = [f"N{k}" for k in range(1, len(rc) + 1)] + ["TAMB"]
    for k, (r, c) in enumerate(zip(rc, cc), start=1):
        lines.append(f"C{k} {nodes[k - 1]} TAMB {FMT.format(c)}")
        lines.append(f"R{k} {nodes[k - 1]} {nodes[k]} {FMT.format(r)}")
    lines += ["E1 T TAMB N1 TAMB 1", f".ENDS {name}"]
    return lines


def _symbol(name, model_file, description):
    """LTspice symbol: P on the left, T on the right, TAMB at the bottom."""
    return "\n".join([
        "Version 4",
        "SymbolType BLOCK",
        "RECTANGLE Normal -96 -48 96 48",
        "WINDOW 0 0 -56 Bottom 2",
        "WINDOW 3 0 56 Top 2",
        f"SYMATTR Value {name}",
        "SYMATTR Prefix X",
        f"SYMATTR ModelFile {model_file}",
        f"SYMATTR Description {description}",
        "PIN -96 0 LEFT 8",
        "PINATTR PinName P",
        "PINATTR SpiceOrder 1",
        "PIN 96 0 RIGHT 8",
        "PINATTR PinName T",
        "PINATTR SpiceOrder 2",
        "PIN 0 48 BOTTOM 8",
        "PINATTR PinName TAMB",
        "PINATTR SpiceOrder 3",
    ]) + "\n"


def _rise_time(tau_min):
    """Rise time of the power step: tau_min / 100 rounded down to a decade,
    between 0.1 us and 1 us (a faster step stops some simulators with
    "timestep too small")."""
    rise = 10.0 ** np.floor(np.log10(tau_min / 100.0))
    return float(min(max(rise, 1e-7), 1e-6))


def _testbench(name, kind, model_file, t_end, tau_min, power, ambient):
    rise = _rise_time(tau_min)
    return [f"* {name}: test bench of the {kind} thermal model",
            f"* Power step of {FMT.format(power)} W at t = 0 (rise {FMT.format(rise)} s), "
            f"ambient {FMT.format(ambient)} degC.",
            "* 1 A = 1 W, 1 V = 1 degC. V(T) is the temperature, "
            "V(T)-V(TAMB) the rise, Zth = rise / power.",
            f".include {model_file}",
            f"VAMB TAMB 0 {FMT.format(ambient)}",
            f"IP 0 P PWL(0 0 {FMT.format(rise)} {FMT.format(power)})",
            f"X1 P T TAMB {name}",
            f".tran {FMT.format(t_end / 1000.0)} {FMT.format(t_end)} 0 {FMT.format(t_end / 10000.0)}",
            f".meas TRAN T_END FIND V(T) AT={FMT.format(t_end)}",
            ".options plotwinsize=0",
            ".end"]


def write_ltspice(Rth_foster, tau_foster, folder=".", base=None, t_end=None,
                  source=None, power=None, ambient=None):
    """Write the LTspice model of a Foster network in ``folder``.

    Parameters
    ----------
    Rth_foster, tau_foster : array_like
        Foster network, K/W and s. Cells with R <= 0 or tau <= 0 are left out.
    folder : str
        Output folder, created if needed.
    base : str, optional
        Name of the model; by default ``base_name(source)``.
    t_end : float, optional
        Duration of the test bench, s; by default 5 times the largest time
        constant.
    source : str, optional
        Input file, written in the headers and used for the default name.
    power, ambient : float, optional
        Power step (W) and ambient (degC) of the test bench; by default
        ``config.LTSPICE_TESTBENCH_POWER`` and ``config.LTSPICE_AMBIENT``.

    Returns
    -------
    LTspiceModel
    """
    R, t = _foster_cells(Rth_foster, tau_foster)
    if R.size == 0:
        raise ValueError("No Foster cell with R > 0 and tau > 0: nothing to export")
    base = base_name(base or source)
    power = config.LTSPICE_TESTBENCH_POWER if power is None else float(power)
    ambient = config.LTSPICE_AMBIENT if ambient is None else float(ambient)
    if t_end is None or not np.isfinite(t_end) or t_end <= 0:
        t_end = 5.0 * t.max()
    os.makedirs(folder, exist_ok=True)

    out = LTspiceModel(base=base)
    origin = os.path.basename(str(source)) if source else "pasted data"
    origin = origin.encode("ascii", "replace").decode("ascii")

    networks = [("FOSTER", "Foster", _foster_subckt(f"{base}_FOSTER", R, t))]
    out.foster_cells = len(R)
    cauer = cauer_cells(R, t)
    if cauer is None:
        out.notes.append("Cauer model not written: the Foster to Cauer conversion gave "
                         "an element that is not positive")
    else:
        networks.append(("CAUER", "Cauer", _cauer_subckt(f"{base}_CAUER", *cauer)))
        out.cauer_cells = len(cauer[0])

    for kind, label, body in networks:
        name = f"{base}_{kind}"
        model_file = f"{name}.net"
        header = [f"* {name}: {label} thermal model identified from {origin}",
                  "* Thermal Impedance Analysis tool (thermal_analysis package)",
                  "* 1 A = 1 W, 1 V = 1 degC, 1 Ohm = 1 K/W, 1 F = 1 J/K",
                  "* Pins: P = power input (current into P), T = temperature output, "
                  "TAMB = ambient",
                  "* V(T) = V(TAMB) + Zth(t) * P(t)", "*"]
        files = {"models": (model_file, header + body),
                 "symbols": (f"{name}.asy", None),
                 "testbenches": (f"{name}_testbench.net",
                                 _testbench(name, label, model_file, t_end, t.min(),
                                            power, ambient))}
        for attr, (file_name, lines) in files.items():
            path = os.path.join(folder, file_name)
            with open(path, "w", encoding="ascii", newline="\n") as f:
                if lines is None:
                    f.write(_symbol(name, model_file, f"{label} thermal network of {base}"))
                else:
                    f.write("\n".join(lines) + "\n")
            getattr(out, attr)[kind] = path
    return out
