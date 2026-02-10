import pytest

from ndt2ud.parse_conllu import validate_conll_lines


def test_if_conll_line_is_valid():
    lines = [
        "1	ja	ja	INTJ	_	_	6	discourse	_	hov",
        "2	##	##	pause	_	_	3	IK	_	hov",
        "3	det	det	PRON	_	Gender=Neut|Person=3|PronType=Prs	6	expl	_	hov",
    ]

    output = validate_conll_lines(lines)
    assert len(output) == len(lines)
    for line, resulting_line in zip(lines, output):
        assert line == resulting_line, f"Expected: {line}, but got: {resulting_line}"


def test_if_conll_line_is_invalid():
    lines = [
        "1	ja	ja	INTJ	_	_	6	discourse	_	hov",
        "2	##	##	pause	_	_	3	IK	_	hov",
        "3	det	det	PRON	_	Gender=	hov",
    ]

    with pytest.raises(ValueError) as e:
        output = validate_conll_lines(lines)
    assert e.type is ValueError
