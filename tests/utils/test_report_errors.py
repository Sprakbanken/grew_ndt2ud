import pandas as pd
import pytest

from ndt2ud.utils import report_errors


def test_report_errors_catches_all_message_pieces(tmp_path):
    report_file = tmp_path / "report.txt"
    text = "[File aal_uio_02_output.conllu Line 1816 Sent 110]: [L2 Syntax invalid-deprel] Invalid DEPREL value 'SLETT'. Only lowercase English letters or a colon are expected."
    report_file.write_text(text)
    assert report_file.read_text() == text

    result = report_errors(report_file)
    row = result.iloc[0]

    assert len(result.columns) == 8
    assert row.file == "aal_uio_02_output.conllu"
    assert row.line == "1816"
    assert row.sent == "110"
    assert row.node == None
    assert row.error_level == "L2"
    assert row.error_class == "Syntax"
    assert row.error_name == "invalid-deprel"


def test_report_errors(tmp_path):
    report = (
        "[File file1.conllu Line 1 Sent 1 Node 2]: [L1 CLASS1 ERR1] message1\n"
        "[File file1.conllu Line 2 Sent 2 Node 3]: [L2 CLASS2 ERR2] message2\n"
        "[File file1.conllu Line 1 Sent 1 Node 2]: [L1 CLASS1 ERR1] message1\n"
    )
    report_file = tmp_path / "report.txt"
    report_file.write_text(report, encoding="utf-8")
    df = report_errors(report_file, output_file="-")
    assert isinstance(df, pd.DataFrame)
    assert {"error_level", "error_class", "error_name"}.issubset(df.columns)
    assert (df["error_level"] == "L1").sum() == 2
