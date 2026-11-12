# -*- coding: utf-8 -*-
"""Reading input curves and writing results.

Same formats and rules as the stand-alone Zth_to_Foster tool:

* ``read_table``: command line (.xlsx/.csv with a header, other files as
  plain numbers);
* ``read_for_window`` and ``parse_text``: window (Load File, data box);
* ``results_table``: table of Copy All Data, and of Export All Data as CSV;
* ``export_excel``: Excel workbook of Export All Data and of the command
  line, one sheet per result;
* ``write_cli_outputs``: text files and plot scripts of the command line;
* ``export_pdf``: PDF report of the window.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

from .utils import pad


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

def read_table(datafile):
    """Command line: read (time, Zth) from a file, keep time > 0."""
    if datafile.lower().endswith((".xlsx", ".csv")):
        df = pd.read_excel(datafile) if datafile.lower().endswith(".xlsx") else pd.read_csv(datafile)
        if "time" in df.columns and "Zth" in df.columns:
            time, z_meas = df["time"].values, df["Zth"].values
        else:
            time, z_meas = df.iloc[:, 0].values, df.iloc[:, 1].values
    else:
        data = np.loadtxt(datafile)
        time, z_meas = data[:, 0], data[:, 1]
    mask = time > 0
    return time[mask], z_meas[mask]


def read_for_window(filename):
    """Window, Load File: first two columns of a .xlsx, .csv or .txt file."""
    if filename.endswith(".xlsx"):
        df = pd.read_excel(filename)
    else:
        sep = "\t" if filename.endswith(".txt") else ","
        df = pd.read_csv(filename, sep=sep)
    return df.iloc[:, 0], df.iloc[:, 1]


def parse_text(text):
    """Window, data box: skip the first line, accept decimal commas, keep time > 0."""
    lines = text.strip().splitlines()[1:]
    data = []
    for line in lines:
        line = line.replace(",", ".")  # decimal commas (French Excel)
        parts = line.strip().split()
        if len(parts) < 2:
            continue  # empty or incomplete line
        try:
            data.append([float(parts[0]), float(parts[1])])
        except ValueError:
            continue  # non-numeric line (e.g. repeated header)
    data = np.array(data)
    time, z_meas = data[:, 0], data[:, 1]
    mask = time > 0
    return time[mask], z_meas[mask]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def results_table(res, diff_name="dC/dR"):
    """All results, every column padded or cut to the length of time."""
    n = len(res.time)
    return pd.DataFrame({
        "time": res.time,
        "Z_meas": res.Z_meas,
        "Z_foster": res.Z_foster,
        "Rth_foster": pad(res.Rth_foster, n),
        "tau_foster": pad(res.tau_foster, n),
        "R_cauer": pad(res.Rth_cauer, n),
        "C_cauer": pad(res.C_cauer, n),
        "Rth_cum": pad(res.Rth_cum, n),
        "C_cum": pad(res.C_cum, n),
        "Rth_diff": pad(res.Rth_diff, n),
        diff_name: pad(res.dC_dRth, n),
    })


def _excel_sheets(res, diff_unit, source=None):
    """Sheets of the Excel workbook: (name, DataFrame), each at its own length."""
    R = np.asarray(res.Rth_foster, dtype=float)
    tau = np.asarray(res.tau_foster, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        C = np.where(R > 0, tau / R, np.nan)
    order = np.argsort(tau)
    source = source or getattr(res, "current_file", None)
    summary = [
        ("Input", os.path.basename(str(source)) if source else "pasted data", ""),
        ("Points", len(res.time), ""),
        ("First time", float(res.time[0]), "s"),
        ("Last time", float(res.time[-1]), "s"),
        ("Last Zth", float(res.Z_meas[-1]), "K/W"),
        ("Foster cells", len(R), ""),
        ("Rth, sum of the Foster R", float(R.sum()), "K/W"),
        ("Cauer cells", len(res.Rth_cauer), ""),
        ("Richardson-Lucy iterations M", getattr(res, "M_opt", None), ""),
    ]
    zth = pd.DataFrame({"time (s)": res.time, "Z_meas (K/W)": res.Z_meas,
                        "Z_foster (K/W)": res.Z_foster})
    foster = pd.DataFrame({"cell": np.arange(1, len(R) + 1),
                           "Rth_foster (K/W)": R[order], "tau_foster (s)": tau[order],
                           "C_foster (J/K)": C[order]})
    cauer = pd.DataFrame({"cell": np.arange(1, len(res.Rth_cauer) + 1),
                          "R_cauer (K/W)": res.Rth_cauer, "C_cauer (J/K)": res.C_cauer})
    cum = pd.DataFrame({"R_cum (K/W)": res.Rth_cum, "C_cum (J/K)": res.C_cum})
    diff = pd.DataFrame({"R_diff (K/W)": res.Rth_diff, f"dC/dR ({diff_unit})": res.dC_dRth})
    return [("Summary", pd.DataFrame(summary, columns=["Quantity", "Value", "Unit"])),
            ("Zth", zth), ("Foster", foster), ("Cauer", cauer),
            ("Cumulative SF", cum), ("Differential SF", diff)]


def export_excel(res, filename, diff_unit="W²·s/K²", source=None):
    """Excel workbook of the results, one sheet per table, full precision.

    Sheets: Summary, Zth (time, Z_meas, Z_foster), Foster (cells sorted by
    time constant, with C = tau / R), Cauer (junction first), Cumulative SF,
    Differential SF. Unlike the CSV export, each table keeps its own length.
    """
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        for name, df in _excel_sheets(res, diff_unit, source):
            df.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            sheet.freeze_panes = "A2"
            for k, col in enumerate(df.columns):
                width = max([len(str(col)), 13] +
                            [len(v) for v in df.iloc[:, k] if isinstance(v, str)])
                sheet.column_dimensions[chr(ord("A") + k)].width = width + 2
            for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    if isinstance(cell.value, float):
                        cell.number_format = "0.000000E+00"


def two_columns(a, b):
    """Text of a result table: two tab-separated columns, 6 significant digits."""
    return "".join(f"{x:.6g}\t{y:.6g}\n" for x, y in zip(a, b))


def plot_code(xname, yname, title, xdata, ydata):
    """Python script that plots one curve (the *_plot.txt files of the CLI)."""
    return f"""
import matplotlib.pyplot as plt
import numpy as np
{xname} = np.array({repr(np.asarray(xdata).tolist())})
{yname} = np.array({repr(np.asarray(ydata).tolist())})
plt.figure()
plt.plot({xname}, {yname}, label='{title}')
plt.xlabel('{xname}')
plt.ylabel('{yname}')
plt.title('{title}')
plt.legend()
plt.grid(True)
plt.show()
"""


def write_cli_outputs(res, folder="."):
    """Text tables and plot scripts of the command line, written in folder."""
    def path(name):
        return os.path.join(folder, name)

    np.savetxt(path("foster.txt"), np.column_stack([res.Rth_foster, res.tau_foster]),
               header="Rth_foster tau_foster")
    np.savetxt(path("cauer.txt"), np.column_stack([res.Rth_cauer, res.C_cauer]),
               header="Rth_cauer C_cauer")
    np.savetxt(path("cumul.txt"), np.column_stack([res.Rth_cum, res.C_cum]), header="R_cum C_cum")
    np.savetxt(path("diff.txt"), np.column_stack([res.Rth_diff, res.dC_dRth]), header="Rdiff dC_dR")
    plots = [
        ("zth_plot.txt", "time", "Z_meas", "Zth", res.time, res.Z_meas),
        ("dz_plot.txt", "z", "dZ_dz", "dZ/dln(t)", res.z, res.dZ_dz),
        ("spectrum_plot.txt", "time", "dZ_dz", "Spectrum R", res.time, res.dZ_dz),
        ("cumul_plot.txt", "R_cum", "C_cum", "Cumulative Structure", res.Rth_cum, res.C_cum),
        ("diff_plot.txt", "Rdiff", "dC_dR", "Differential Structure", res.Rth_diff, res.dC_dRth),
    ]
    for name, xname, yname, title, x, y in plots:
        with open(path(name), "w") as f:
            f.write(plot_code(xname, yname, title, x, y))


def export_pdf(res, filename, diff_unit="J/K²"):
    """PDF report of the window: five plots, then the tables."""
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.figure import Figure

    with PdfPages(filename) as pdf:
        def page(plot, grid_both):
            fig = Figure(figsize=(8, 6))
            ax = fig.add_subplot(111)
            plot(ax)
            ax.grid(True, which="both") if grid_both else ax.grid(True)
            pdf.savefig(fig)
            plt.close(fig)

        def zth(ax):
            ax.plot(res.time, res.Z_meas, label="Measured")
            ax.plot(res.time, res.Z_foster, "--", label="Foster")
            ax.set(title="Thermal Impedance Zth", xscale="log", xlabel="time (s)", ylabel="Zth")
            ax.legend()

        def derivative(ax):
            ax.plot(res.z, res.dZ_dz)
            ax.set(title="Derivative of Zth (dZ/dln(t))", xlabel="ln(t)", ylabel="dZ/dln(t)")

        def spectrum(ax):
            ax.plot(res.z, res.R_spec)
            ax.set(title="Thermal Resistance Spectrum R(ln(t))", xlabel="ln(t)", ylabel="R(ln(t))")

        def cumulative(ax):
            ax.plot(res.Rth_cum, res.C_cum, marker="o")
            ax.set(xscale="log", yscale="log", xlabel="Cumulative thermal resistance RΣ [K/W]",
                   ylabel="Cumulative thermal capacitance CΣ [J/K]",
                   title="Cumulative structure function")

        def differential(ax):
            ax.step(res.Rth_diff, res.dC_dRth, where="post")
            ax.set(xscale="log", yscale="log", xlabel="Cumulative thermal resistance RΣ [K/W]",
                   ylabel=f"dCΣ / dRΣ [{diff_unit}]", title="Differential structure function")

        for plot, grid_both in ((zth, False), (derivative, False), (spectrum, False),
                                (cumulative, True), (differential, True)):
            page(plot, grid_both)

        _table_to_pdf(pd.DataFrame({"Rth_foster": res.Rth_foster, "tau_foster": res.tau_foster}),
                      pdf, "Foster Poles")
        _table_to_pdf(pd.DataFrame({"Rth_cauer": res.Rth_cauer, "C_cauer": res.C_cauer}),
                      pdf, "Cauer Poles")
        _table_to_pdf(pd.DataFrame({"Rth_cum": res.Rth_cum, "C_cum": res.C_cum}),
                      pdf, "Cumulative Structure Function")
        _table_to_pdf(pd.DataFrame({"Rth_diff": res.Rth_diff, "dC/dR": res.dC_dRth}),
                      pdf, "Differential Structure Function")
        main = pd.DataFrame({"Point n°": np.arange(1, len(res.time) + 1), "time": res.time,
                             "Z_meas": res.Z_meas, "Z_foster": res.Z_foster})
        _table_to_pdf(main, pdf, "Main Data", rows_per_page=50, figsize=(8.27, 11.69),
                      fontsize=5, scale=(0.9, 1))


def _table_to_pdf(df, pdf, title, rows_per_page=50, figsize=(10, 6), fontsize=5, scale=(1, 1.2)):
    """Export a DataFrame as table pages, rows_per_page rows per page."""
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    n_pages = int(np.ceil(len(df) / rows_per_page))
    for i in range(n_pages):
        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.axis("off")
        chunk = df.iloc[i * rows_per_page:(i + 1) * rows_per_page]
        table = ax.table(cellText=chunk.round(6).values, colLabels=chunk.columns,
                         loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(fontsize)
        table.scale(*scale)
        ax.set_title(title)
        pdf.savefig(fig)
        plt.close(fig)
