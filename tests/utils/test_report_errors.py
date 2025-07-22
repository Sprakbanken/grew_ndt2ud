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
