"""Web version of the Thermal Impedance Analysis tool (Zth to Foster and Cauer).

Run locally, from the repository root:

    pip install -r webapp/requirements.txt
    streamlit run webapp/app.py
"""

from __future__ import annotations

import io

import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.figure import Figure

from service import (ROOT, InputError, load_table, max_deviation_percent, results_zip, run)
from thermal_analysis import config

# Fill in once the code is public, e.g. "https://github.com/<account>/Thermal_Impedance_Analysis"
REPO_URL = "https://thermalimpedanceanalysis.streamlit.app/"

EXAMPLES = sorted((ROOT / "thermal_analysis" / "input_data").glob("*.xlsx"))
DEFAULT_EXAMPLE = "MEAS_IGBT.xlsx"

st.set_page_config(page_title="Zth to Foster/Cauer", layout="wide")


@st.cache_data(show_spinner=False, max_entries=8)
def analyse_file(raw: bytes, filename: str, n_branches: int):
    time, z = load_table(io.BytesIO(raw), filename)
    res = run(time, z, n_branches=n_branches)
    return res, results_zip(res, filename)


def fig_zth(res) -> Figure:
    fig = Figure(figsize=(6.4, 4.2))
    ax = fig.subplots()
    ax.semilogx(res.time, res.Z_meas, ".", ms=3, color="0.45", label="Data")
    ax.semilogx(res.time, res.Z_foster, "-", lw=1.8, color="C3",
                label=f"Foster, {len(res.Rth_foster)} cells")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("$Z_{th}$ (K/W)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig


def fig_spectrum(res) -> Figure:
    fig = Figure(figsize=(6.4, 4.2))
    ax = fig.subplots()
    ax.semilogx(np.exp(res.z), res.R_spec, color="C0", label="Spectrum of the data")
    ax.semilogx(np.exp(res.z_rec), res.R_rec, "--", color="C3", label="Spectrum of the Foster curve")
    ax.set_xlabel("time constant (s)")
    ax.set_ylabel("R (K/W per unit of ln t)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig


def fig_structure(x, y, xlabel, ylabel) -> Figure:
    fig = Figure(figsize=(6.4, 4.2))
    ax = fig.subplots()
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    ax.loglog(x[keep], y[keep], color="C0", lw=1.8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------

st.title("Thermal impedance: Zth(t) to Foster and Cauer networks")
st.write(
    "Upload a measured or simulated thermal impedance curve. The tool identifies a "
    "Foster RC network (the number of cells comes from the data), converts it to a "
    "Cauer network, computes the structure functions of the heat path and writes "
    "LTspice models of both networks."
)
if REPO_URL:
    st.caption(f"Source code, method and documentation: [{REPO_URL}]({REPO_URL})")

with st.sidebar:
    st.header("Input")
    mode = st.radio("Data", ["Example file", "Upload a file"], label_visibility="collapsed")
    raw, filename = None, None
    if mode == "Upload a file":
        up = st.file_uploader("Zth(t) curve", type=["xlsx", "csv", "txt"])
        st.caption(
            "Two columns: time in s, then Zth in K/W (or columns named `time` and `Zth`). "
            "Files are processed in memory and are not stored."
        )
        if up is not None:
            raw, filename = up.getvalue(), up.name
    else:
        names = [p.name for p in EXAMPLES]
        index = names.index(DEFAULT_EXAMPLE) if DEFAULT_EXAMPLE in names else 0
        filename = st.selectbox("Example", names, index=index)
        raw = (ROOT / "thermal_analysis" / "input_data" / filename).read_bytes()
    n_branches = st.slider("Maximum number of Foster cells", 3, 20, config.DEFAULT_MAX_BRANCHES)
    go = st.button("Process", type="primary", disabled=raw is None)

if go and raw is not None:
    try:
        with st.spinner("Identifying the network. This takes 10 to 60 s."):
            st.session_state["res"], st.session_state["zip"] = analyse_file(raw, filename, n_branches)
            st.session_state["res_name"] = filename
    except InputError as exc:
        st.session_state.pop("res", None)
        st.error(str(exc))

res = st.session_state.get("res")
if res is None:
    st.info("Choose a file in the sidebar, then click **Process**.")
    st.stop()

dev = max_deviation_percent(res)
c1, c2, c3 = st.columns(3)
c1.metric("File", st.session_state.get("res_name", ""))
c2.metric("Foster cells", len(res.Rth_foster))
c3.metric("Largest gap to the data", f"{dev:.2f} % of max Zth")

tab_zth, tab_net, tab_struct, tab_dl = st.tabs(
    ["Zth and spectrum", "Networks", "Structure functions", "Download"]
)

with tab_zth:
    a, b = st.columns(2)
    a.pyplot(fig_zth(res), clear_figure=True)
    b.pyplot(fig_spectrum(res), clear_figure=True)

with tab_net:
    order = np.argsort(res.tau_foster)
    foster = pd.DataFrame({
        "Rth (K/W)": res.Rth_foster[order],
        "tau (s)": res.tau_foster[order],
        "Cth (J/K)": res.C_foster[order],
    })
    cauer = pd.DataFrame({"Rth (K/W)": res.Rth_cauer, "Cth (J/K)": res.C_cauer})
    a, b = st.columns(2)
    a.subheader("Foster network")
    a.dataframe(foster.style.format("{:.4e}"), hide_index=True)
    b.subheader("Cauer network")
    b.dataframe(cauer.style.format("{:.4e}"), hide_index=True)
    st.caption(f"Total thermal resistance of the Foster network: {res.Rth_foster.sum():.4g} K/W.")

with tab_struct:
    a, b = st.columns(2)
    a.pyplot(fig_structure(res.Rth_cum, res.C_cum,
                           "cumulative thermal resistance (K/W)",
                           "cumulative thermal capacitance (J/K)"), clear_figure=True)
    b.pyplot(fig_structure(res.Rth_diff, res.dC_dRth,
                           "cumulative thermal resistance (K/W)",
                           f"dC/dR ({config.DIFFERENTIAL_UNIT_LABEL})"), clear_figure=True)
    st.caption("Computed from the Cauer network, as the command line does. The desktop window "
               "uses PyRth for this step and gives slightly different curves.")

with tab_dl:
    st.download_button("Download the results (.zip)", st.session_state["zip"],
                       file_name="thermal_analysis_results.zip", mime="application/zip")
    st.caption("foster.txt, cauer.txt, cumul.txt, diff.txt, an Excel workbook with one sheet per table, "
               "and the LTspice model, symbol and test bench of the Foster and of the Cauer network.")

st.divider()
st.caption(
    "Research code, provided as is. Check the identified network against your data "
    "before using it in a design."
)
