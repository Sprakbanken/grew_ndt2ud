from pathlib import Path

import ndt2ud


def test_validate_runs_and_writes_report(monkeypatch, tmp_path):
    # Prepare dummy files
    treebank_file = tmp_path / "treebank.conllu"
    treebank_file.write_text("dummy treebank")
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
        treebank_file, report_file, path_to_script=str(script_file), overwrite=True
    )
    # Check that report file was written
    assert report_file.exists()
    assert report_file.read_text() == "validation error"


def test_validate_missing_script_logs_error(monkeypatch, tmp_path):
    treebank_file = tmp_path / "treebank.conllu"
    treebank_file.write_text("dummy treebank")
    report_file = tmp_path / "report.txt"
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
        treebank_file, report_file, path_to_script=str(script_file), overwrite=True
    )
    assert "Can't find the path to the validation script" in called.get("error", "")
    # Should still write the report file
    assert report_file.exists()
    assert report_file.read_text() == "validation error"


def test_validate_appends_when_overwrite_false(monkeypatch, tmp_path):
    # given
    treebank_file = tmp_path / "treebank.conllu"
    treebank_file.write_text("dummy treebank")
    report_file = tmp_path / "report.txt"
    report_file.write_text("existing\n")
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

    # Patch utils.report_errors to record call
    monkeypatch.setattr(ndt2ud.utils, "report_errors", lambda path: None)

    # when
    ndt2ud.validate(
        treebank_file, report_file, path_to_script=str(script_file), overwrite=False
    )
    # then
    # Should append to the file
    assert report_file.read_text() == "existing\nvalidation error"
