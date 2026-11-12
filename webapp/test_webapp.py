"""Checks for the web app. From the repository root:

    pip install pytest
    pytest webapp -q
"""

import io
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import service  # noqa: E402

SAMPLE = ROOT / "thermal_analysis" / "input_data" / "MEAS_IGBT.xlsx"


@pytest.fixture(scope="module")
def result():
    t, z = service.load_table(SAMPLE, SAMPLE.name)
    return service.run(t, z, n_branches=10)


def test_same_tables_as_the_command_line(result, tmp_path):
    """The web analysis must give the numbers of the command line."""
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    subprocess.run(
        [sys.executable, "-m", "thermal_analysis", "-file", str(SAMPLE)],
        cwd=tmp_path, env=env, check=True, capture_output=True, timeout=600,
    )
    blob = service.results_zip(result, SAMPLE.name)
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = set(zf.namelist())
        assert {"foster.txt", "cauer.txt", "cumul.txt", "diff.txt",
                "MEAS_IGBT_results.xlsx", "MEAS_IGBT_FOSTER.net", "MEAS_IGBT_CAUER.net"} <= names
        assert len(names) == 4 + 1 + 6
        for name in ("foster.txt", "cauer.txt", "cumul.txt", "diff.txt"):
            expected = np.loadtxt(tmp_path / name)
            got = np.loadtxt(io.StringIO(zf.read(name).decode()))
            assert got.shape == expected.shape, name
            np.testing.assert_allclose(got, expected, rtol=1e-6, err_msg=name)


def test_igbt_sample_matches_the_documentation(result):
    assert len(result.Rth_foster) == 7
    assert service.max_deviation_percent(result) < 1.0


@pytest.mark.parametrize("name, content", [
    ("bad.docx", b"x"),
    ("one_column.csv", b"1\n2\n3\n"),
    ("too_short.csv", b"time,Zth\n1,1\n2,2\n3,3\n"),
    ("text.csv", b"time,Zth\n" + b"\n".join(b"a,b" for _ in range(40))),
])
def test_bad_files_give_a_clear_error(name, content):
    with pytest.raises(service.InputError):
        service.load_table(io.BytesIO(content), name)


def test_flat_curve_gives_an_error_not_a_crash():
    t = np.logspace(-3, 2, 60)
    with pytest.raises(service.InputError):
        service.run(t, np.ones_like(t))


def test_page_runs_on_the_example_file():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(HERE / "app.py"), default_timeout=300).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    assert not at.error
    assert len(at.dataframe) == 2          # Foster and Cauer tables
    assert at.metric[1].value == "7"       # number of Foster cells
