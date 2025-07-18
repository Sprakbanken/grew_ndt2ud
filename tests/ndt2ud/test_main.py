import sys
from unittest import mock

import pytest

import ndt2ud.__init__ as ndt2ud_init


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
@mock.patch("ndt2ud.__init__.validate")
@mock.patch("ndt2ud.__init__.utils.report_errors")
def test_main_single_file_conversion(
    mock_report_errors,
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
            "-l",
            "nb",
            "-i",
            str(fake_conll_file),
            "-o",
            str(ud_file),
            "-g",
            str(temp_workspace / "src" / "ndt2ud" / "rules" / "NDT_to_UD.grs"),
            "-r",
            str(temp_workspace / "validation-report.txt"),
            "-val",
            str(temp_workspace / "tools" / "validate.py"),
            "-s",
        ]
        with mock.patch.object(sys, "argv", sys_argv):
            ndt2ud_init.main()
        # Should call convert_ndt_to_ud once
        mock_convert_ndt_to_ud.assert_called_once()
        # Should call validate for output file
        mock_validate.assert_called()
        # Should call report_errors
        mock_report_errors.assert_called_once()


@mock.patch("ndt2ud.__init__.convert_ndt_to_ud")
def test_main_input_file_not_exists(mock_convert_ndt_to_ud, temp_workspace):
    with mock.patch.object(
        ndt2ud_init, "__file__", str(temp_workspace / "src" / "ndt2ud" / "__init__.py")
    ):
        sys_argv = [
            "ndt2ud",
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
