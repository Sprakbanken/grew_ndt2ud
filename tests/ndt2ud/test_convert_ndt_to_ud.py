import os
import shutil
import tempfile
from pathlib import Path

import pytest

import ndt2ud


@pytest.fixture
def mock_dependencies(monkeypatch, tmp_path):
    # Mock parse_conll_file
    monkeypatch.setattr(ndt2ud, "parse_conll_file", lambda path: ["dummy_conllu_data"])
    # Mock convert_morphology
    monkeypatch.setattr(ndt2ud, "convert_morphology", lambda data: ["morphdata"])
    # Mock write_conll
    monkeypatch.setattr(ndt2ud, "write_conll", lambda data, path, drop_comments: None)
    # Mock utils.set_spaceafter_from_text
    monkeypatch.setattr(ndt2ud.utils, "set_spaceafter_from_text", lambda x: x)
    # Mock CorpusDraft

    class DummyDraft:
        def __init__(self, path):
            pass

        def map(self, func, in_place):
            pass

    monkeypatch.setattr(ndt2ud, "CorpusDraft", DummyDraft)
    # Mock Corpus

    class DummyCorpus:
        def __init__(self, arg):
            pass

        def to_conll(self):
            return "conll"

    monkeypatch.setattr(ndt2ud, "Corpus", DummyCorpus)
    # Mock GRS

    class DummyGRS:
        def __init__(self, path):
            pass

        def apply(self, corpus, strat):
            return DummyCorpus(None)

    monkeypatch.setattr(ndt2ud, "GRS", DummyGRS)
    # Mock utils.udapi_fixes
    monkeypatch.setattr(ndt2ud.utils, "udapi_fixes", lambda infile, outfile: None)
    # Create a dummy grew rules file
    grs_path = tmp_path / "rules.grs"
    grs_path.write_text("dummy rules")
    # Create a dummy input file
    input_file = tmp_path / "input.conllu"
    input_file.write_text("dummy input")
    # Output file
    output_file = tmp_path / "output.conllu"
    yield {
        "input_file": str(input_file),
        "language": "nb",
        "output_file": str(output_file),
        "grs_path": str(grs_path),
        "tmp_path": tmp_path,
    }
    # Cleanup
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_convert_ndt_to_ud_creates_output_file(mock_dependencies):
    args = mock_dependencies
    ndt2ud.convert_ndt_to_ud(
        args["input_file"], args["language"], args["output_file"], args["grs_path"]
    )
    assert Path(args["output_file"]).exists()
    # Check that the output file contains the expected replaced string
    with open(args["output_file"]) as f:
        content = f.read()
    # Since we mock everything, the file may be empty or contain "conll"
    assert isinstance(content, str)
    assert content == "conll"


def test_convert_ndt_to_ud_missing_grs(mock_dependencies, monkeypatch, tmp_path):
    # Setup as above, but the grs file is "missing"
    grs_path = tmp_path / "missing_rules.grs"

    # Patch logging.error to capture calls
    called = {}

    def fake_error(msg, *args, **kwargs):
        called["error"] = msg

    monkeypatch.setattr(ndt2ud.logging, "error", fake_error)

    args = mock_dependencies
    ndt2ud.convert_ndt_to_ud(
        args["input_file"], args["language"], args["output_file"], str(grs_path)
    )
    assert "not found" in called.get("error", "")
    assert not Path(args["output_file"]).exists()
