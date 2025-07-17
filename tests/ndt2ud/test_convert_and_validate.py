import os
import shutil
import sys
import tempfile
import types
from pathlib import Path

import pytest

import ndt2ud.__init__ as ndt2ud_init


@pytest.fixture(autouse=True)
def patch_logging(monkeypatch):
    # Prevent actual logging to file
    monkeypatch.setattr(ndt2ud_init.logging, "basicConfig", lambda *a, **k: None)
    monkeypatch.setattr(ndt2ud_init.logging, "info", lambda *a, **k: None)
    monkeypatch.setattr(ndt2ud_init.logging, "error", lambda *a, **k: None)


@pytest.fixture
def fake_grs_file(tmp_path):
    grs_file = tmp_path / "NDT_to_UD.grs"
    grs_file.write_text("dummy rules")
    return grs_file


@pytest.fixture
def fake_validate_script(tmp_path):
    script = tmp_path / "validate.py"
    script.write_text("print('validate')")
    return script


@pytest.fixture
def fake_conllu_file(tmp_path):
    file = tmp_path / "input.conllu"
    file.write_text("# dummy conllu\n1\ttest\t_\t_\t_\t_\t0\troot\t_\t_")
    return file


@pytest.fixture
def patch_utils(monkeypatch):
    # Patch utils.udapi_fixes to just copy file
    monkeypatch.setattr(
        ndt2ud_init.utils, "udapi_fixes", lambda i, o: shutil.copy(i, o)
    )
    # Patch utils.set_spaceafter_from_text to a no-op
    monkeypatch.setattr(ndt2ud_init.utils, "set_spaceafter_from_text", lambda x: x)


@pytest.fixture
def patch_grewpy(monkeypatch):
    # Patch grewpy.Corpus, CorpusDraft, GRS to minimal mocks
    class DummyCorpus:
        def __init__(self, *a, **k):
            pass

        def to_conll(self):
            return "# dummy conll"

    class DummyCorpusDraft:
        def __init__(self, *a, **k):
            pass

        def map(self, *a, **k):
            return None

    class DummyGRS:
        def __init__(self, *a, **k):
            pass

        def apply(self, corpus, strat=None):
            return DummyCorpus()

    monkeypatch.setattr(ndt2ud_init, "Corpus", DummyCorpus)
    monkeypatch.setattr(ndt2ud_init, "CorpusDraft", DummyCorpusDraft)
    monkeypatch.setattr(ndt2ud_init, "GRS", DummyGRS)
    monkeypatch.setattr(ndt2ud_init.grewpy, "set_config", lambda *a, **k: None)


@pytest.fixture
def patch_parse_conll(monkeypatch):
    monkeypatch.setattr(ndt2ud_init, "parse_conll_file", lambda path: [{"id": 1}])
    monkeypatch.setattr(ndt2ud_init, "convert_morphology", lambda data: data)
    monkeypatch.setattr(
        ndt2ud_init,
        "write_conll",
        lambda data, path, drop_comments: Path(path).write_text("# dummy conll"),
    )


@pytest.fixture
def patch_subprocess(monkeypatch):
    class DummyCompleted:
        def __init__(self):
            self.stderr = "validation error"

    monkeypatch.setattr(ndt2ud_init.subprocess, "run", lambda *a, **k: DummyCompleted())


def run_with_args(args, func):
    old_argv = sys.argv
    sys.argv = ["prog"] + args
    try:
        func()
    finally:
        sys.argv = old_argv


def test_convert_and_validate_file(
    tmp_path,
    fake_conllu_file,
    fake_grs_file,
    fake_validate_script,
    patch_utils,
    patch_grewpy,
    patch_parse_conll,
    patch_subprocess,
):
    output_file = tmp_path / "out.conllu"
    report_file = tmp_path / "report.txt"
    args = [
        "-l",
        "nb",
        "-i",
        str(fake_conllu_file),
        "-o",
        str(output_file),
        "-r",
        str(report_file),
        "-val",
        str(fake_validate_script),
        "-g",
        str(fake_grs_file),
    ]
    run_with_args(args, ndt2ud_init.main)
    assert output_file.exists()
    assert report_file.exists()
    assert "# dummy conll" in output_file.read_text()
    assert "validation error" in report_file.read_text()


def test_convert_and_validate_directory(
    tmp_path,
    fake_grs_file,
    fake_validate_script,
    patch_utils,
    patch_grewpy,
    patch_parse_conll,
    patch_subprocess,
):
    # Create directory with two .conllu files
    input_dir = tmp_path / "indir"
    input_dir.mkdir()
    file1 = input_dir / "a.conllu"
    file2 = input_dir / "b.conll"
    file1.write_text("# dummy1")
    file2.write_text("# dummy2")
    output_file = tmp_path / "outdir" / "out.conllu"
    report_file = tmp_path / "report.txt"
    args = [
        "-l",
        "nn",
        "-i",
        str(input_dir),
        "-o",
        str(output_file),
        "-r",
        str(report_file),
        "-val",
        str(fake_validate_script),
        "-g",
        str(fake_grs_file),
    ]
    run_with_args(args, ndt2ud_init.main)
    # Output files should exist for each input
    out_dir = output_file.parent
    assert (out_dir / "a.conllu").exists()
    assert (out_dir / "b.conll").exists()
    assert report_file.exists()
    assert "validation error" in report_file.read_text()


def test_convert_and_validate_missing_input(
    monkeypatch, tmp_path, fake_grs_file, fake_validate_script
):
    # Patch convert_ndt_to_ud and validate to fail if called
    monkeypatch.setattr(
        ndt2ud_init,
        "convert_ndt_to_ud",
        lambda *a, **k: pytest.fail("Should not be called"),
    )
    monkeypatch.setattr(
        ndt2ud_init, "validate", lambda *a, **k: pytest.fail("Should not be called")
    )
    missing_file = tmp_path / "doesnotexist.conllu"
    args = [
        "-l",
        "nb",
        "-i",
        str(missing_file),
        "-g",
        str(fake_grs_file),
        "-val",
        str(fake_validate_script),
    ]
    run_with_args(args, ndt2ud_init.main)
