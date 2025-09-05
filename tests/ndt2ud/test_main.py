import sys
import types
from pathlib import Path
from unittest import mock

import pytest

import ndt2ud.__init__ as ndt2ud_init


@pytest.fixture
def fake_args_convert(tmp_path):
    # Simulate argparse.Namespace for convert subcommand
    args = types.SimpleNamespace()
    args.language = "nb"
    args.ndt_file = tmp_path / "input.conllu"
    args.ndt_file.write_text("# sample conllu\n")
    args.output = tmp_path / "output"
    args.grew_rules = tmp_path / "rules.grs"
    args.grew_rules.write_text("GRS rules")
    args.validate = False
    args.func = mock.Mock()
    args.verbose = 0
    args._get_kwargs = lambda: [
        ("language", args.language),
        ("ndt_file", args.ndt_file),
        ("output", args.output),
        ("grew_rules", args.grew_rules),
        ("validate", args.validate),
    ]
    return args


@pytest.fixture
def fake_args_validate(tmp_path):
    args = types.SimpleNamespace()
    args.ud_path = tmp_path / "output.conllu"
    args.report_file = tmp_path / "report.txt"
    args.validation_script = tmp_path / "validate.py"
    args.summarize = None
    args.func = mock.Mock()
    args.verbose = 0
    args._get_kwargs = lambda: [
        ("ud_path", args.ud_path),
        ("report_file", args.report_file),
        ("validation_script", args.validation_script),
        ("summarize", args.summarize),
    ]
    return args


@mock.patch("ndt2ud.__init__.argparse.ArgumentParser", autospec=True)
def test_main_convert_calls_func(parser_patch, fake_args_convert):
    parser_patch.return_value.parse_args.return_value = fake_args_convert
    # Patch print to capture output
    with mock.patch("builtins.print") as mock_print:
        ndt2ud_init.main()
        fake_args_convert.func.assert_called_once_with(fake_args_convert)
        mock_print.assert_any_call("Done!")


@mock.patch("ndt2ud.__init__.argparse.ArgumentParser", autospec=True)
def test_main_validate_calls_func(parser_patch, monkeypatch, fake_args_validate):
    parser_patch.return_value.parse_args.return_value = fake_args_validate
    monkeypatch.setattr(ndt2ud_init.logging, "basicConfig", lambda **kwargs: None)
    monkeypatch.setattr(ndt2ud_init.logging, "info", lambda *a, **k: None)
    with mock.patch("builtins.print") as mock_print:
        ndt2ud_init.main()
        fake_args_validate.func.assert_called_once_with(fake_args_validate)
        mock_print.assert_any_call("Done!")


@mock.patch("ndt2ud.__init__.argparse.ArgumentParser", autospec=True)
def test_main_sets_log_level(parser_patch, monkeypatch, fake_args_convert):
    parser_patch.return_value.parse_args.return_value = fake_args_convert
    called = {}

    def fake_basicConfig(level, **kwargs):
        called["level"] = level

    monkeypatch.setattr(ndt2ud_init.logging, "basicConfig", fake_basicConfig)
    monkeypatch.setattr(ndt2ud_init.logging, "info", lambda *a, **k: None)
    with mock.patch("builtins.print"):
        ndt2ud_init.main()
    assert called["level"] == ndt2ud_init.logging.ERROR


@mock.patch("ndt2ud.__init__.argparse.ArgumentParser", autospec=True)
def test_main_debug_verbose_log_level(parser_patch, monkeypatch, fake_args_convert):
    fake_args_convert.verbose = 2
    parser_patch.return_value.parse_args.return_value = fake_args_convert
    called = {}

    def fake_basicConfig(level, **kwargs):
        called["level"] = level

    monkeypatch.setattr(ndt2ud_init.logging, "basicConfig", fake_basicConfig)
    monkeypatch.setattr(ndt2ud_init.logging, "info", lambda *a, **k: None)
    with mock.patch("builtins.print"):
        ndt2ud_init.main()
    assert called["level"] == ndt2ud_init.logging.DEBUG


@pytest.fixture
def temp_workspace(tmp_path):
    # Create a fake workspace structure
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "data" / "UD_output").mkdir(parents=True)
    (workspace / "tools").mkdir()
    (workspace / "src" / "ndt2ud" / "rules").mkdir(parents=True)
    # Fake grew rules file
    grew_rules = workspace / "src" / "ndt2ud" / "rules" / "NDT_to_UD.grs"
    grew_rules.write_text("dummy rules")
    # Fake validation script
    validate_script = workspace / "tools" / "validate.py"
    validate_script.write_text("# dummy script")
    return workspace


@mock.patch("ndt2ud.__init__.convert_ndt_to_ud")
@mock.patch("ndt2ud.__init__._validate")
def test_main_convert_single_file(
    mock_validate,
    mock_convert_ndt_to_ud,
    temp_workspace,
    fake_conll_file,
    ud_file,
):
    # Patch __file__ to simulate running from src/ndt2ud/__init__.py
    with mock.patch.object(
        ndt2ud_init, "__file__", str(temp_workspace / "src" / "ndt2ud" / "__init__.py")
    ):
        sys_argv = [
            "ndt2ud",
            "convert",
            "-l",
            "nb",
            "-i",
            str(fake_conll_file),
            "-o",
            str(ud_file),
            "-g",
            str(temp_workspace / "src" / "ndt2ud" / "rules" / "NDT_to_UD.grs"),
            "--validate",
        ]
        with mock.patch.object(sys, "argv", sys_argv):
            ndt2ud_init.main()
        # Should call convert_ndt_to_ud once
        mock_convert_ndt_to_ud.assert_called_once()
        # Should call validate for output file
        mock_validate.assert_called()


@mock.patch("ndt2ud.__init__.convert_ndt_to_ud")
def test_main_convert_input_file_not_exists(mock_convert_ndt_to_ud, temp_workspace):
    with mock.patch.object(
        ndt2ud_init, "__file__", str(temp_workspace / "src" / "ndt2ud" / "__init__.py")
    ):
        sys_argv = [
            "ndt2ud",
            "convert",
            "-l",
            "nb",
            "-i",
            str(temp_workspace / "missing_file.conllu"),
            "-o",
            str(temp_workspace / "data" / "UD_output" / "UD.conllu"),
        ]
        with mock.patch.object(sys, "argv", sys_argv):
            ndt2ud_init.main()
        mock_convert_ndt_to_ud.assert_not_called()


@mock.patch("ndt2ud.__init__.convert_ndt_to_ud")
def test_main_input_dir_no_files(mock_convert_ndt_to_ud, temp_workspace):
    empty_dir = temp_workspace / "empty_input"
    empty_dir.mkdir()
    with mock.patch.object(
        ndt2ud_init, "__file__", str(temp_workspace / "src" / "ndt2ud" / "__init__.py")
    ):
        sys_argv = [
            "ndt2ud",
            "convert",
            "-l",
            "nb",
            "-i",
            str(empty_dir),
            "-o",
            str(temp_workspace / "data" / "UD_output" / "UD.conllu"),
        ]
        with mock.patch.object(sys, "argv", sys_argv):
            ndt2ud_init.main()
        mock_convert_ndt_to_ud.assert_not_called()


@mock.patch("ndt2ud.__init__.convert_ndt_to_ud")
def test_main_input_dir_with_files(mock_convert_ndt_to_ud, temp_workspace):
    input_dir = temp_workspace / "input_dir"
    input_dir.mkdir()
    file1 = input_dir / "file1.conllu"
    file2 = input_dir / "file2.conll"
    file1.write_text("dummy")
    file2.write_text("dummy")
    with mock.patch.object(
        ndt2ud_init, "__file__", str(temp_workspace / "src" / "ndt2ud" / "__init__.py")
    ):
        sys_argv = [
            "ndt2ud",
            "convert",
            "-l",
            "nn",
            "-i",
            str(input_dir),
            "-o",
            str(temp_workspace / "data" / "UD_output" / "UD.conllu"),
        ]
        with mock.patch.object(sys, "argv", sys_argv):
            ndt2ud_init.main()
        # Should call convert_ndt_to_ud for each file
        assert mock_convert_ndt_to_ud.call_count == 2
