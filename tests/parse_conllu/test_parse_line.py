import pytest

from ndt2ud.parse_conllu import parse_line


def test_if_conll_line_is_valid():
    lines = [
        "5	stedet	sted	subst	_	be|nøyt|ent|appell	16	REP	_	_",
        "6	#	#	pause	_	_	7	IK	_	_",
        "7	nei	nei	interj	_	_	16	INTERJ	_	_",
        "8	det	det	pron	_	nøyt|3|ent|pers	11	REP	_	_",
    ]

    output = parse_line(lines[0])
    assert output == {
        "id": "5",
        "form": "stedet",
        "lemma": "sted",
        "upostag": "subst",
        "xpostag": "_",
        "feats": "be|nøyt|ent|appell",
        "head": "16",
        "deprel": "REP",
        "deps": "_",
        "misc": "_",
    }, f"Expected: {output}, but got: {lines[0]}"
