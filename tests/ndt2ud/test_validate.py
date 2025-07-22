from pathlib import Path

import pytest

import ndt2ud


def test_validate_runs_and_writes_report(monkeypatch, ud_file, tmp_path):
    # Prepare dummy files
    report_file = tmp_path / "report.txt"
    script_file = tmp_path / "validate.py"
    script_file.write_text("dummy script")

    # Patch Path.exists to True for script path
    orig_exists = Path.exists

    def fake_exists(self):
        if str(self) == str(script_file):
            return True
        return orig_exists(self)

    monkeypatch.setattr("pathlib.Path.exists", fake_exists)

    # Patch subprocess.run to return dummy stderr
    class DummyCompleted:
        stderr = "validation error"

    monkeypatch.setattr(ndt2ud.subprocess, "run", lambda *a, **kw: DummyCompleted())

    ndt2ud.validate(
        ud_file, report_file, validation_script=str(script_file), summarize="-"
    )
    # Check that report file was written
    assert report_file.exists()
    assert report_file.read_text() == "validation error"


def test_validate_missing_script_logs_error(monkeypatch, ud_file, tmp_path):
    report_file = tmp_path / "report.txt"
    summary_file = tmp_path / "summary.txt"
    script_file = tmp_path / "missing_validate.py"

    # Patch Path.exists to False for script path
    orig_exists = Path.exists

    def fake_exists(self):
        if str(self) == str(script_file):
            return False
        return orig_exists(self)

    monkeypatch.setattr("pathlib.Path.exists", fake_exists)

    # Patch subprocess.run to return dummy stderr
    class DummyCompleted:
        stderr = "validation error"

    monkeypatch.setattr(ndt2ud.subprocess, "run", lambda *a, **kw: DummyCompleted())

    # Patch logging.error to record call
    called = {}
    monkeypatch.setattr(
        ndt2ud.logging, "error", lambda msg, *a, **kw: called.setdefault("error", msg)
    )

    ndt2ud.validate(
        ud_file,
        report_file,
        validation_script=str(script_file),
        summarize=str(summary_file),
    )
    assert "Can't find the path to the validation script" in called.get("error", "")
    # Should still write the report file
    assert report_file.exists()
    assert report_file.read_text() == "validation error"
    assert summary_file.exists()
