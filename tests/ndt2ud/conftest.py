import pytest


@pytest.fixture
def ndt_file(tmp_path):
    text = """# newpar
# sent_id = ndt_nn
# text = Slik gjer eg det:
1	Slik	slik	adv	adv	_	2	ADV	_	_
2	gjer	gjere	verb	verb	pres	0	FINV	_	_
3	eg	eg	pron	pron	pers|1|eint|hum|nom	2	SUBJ	_	_
4	det	det	pron	pron	pers|3|nøyt|eint	2	DOBJ	_	_
5	:	$:	clb	clb	<kolon>	2	IP	_	_
"""
    file = tmp_path / "ndt.conllu"
    file.write_text(text)
    return file


@pytest.fixture
def ud_file(tmp_path):
    text = """# newpar
# sent_id = ud_nn
# text = Slik gjer eg det:
1	Slik	slik	ADV	adv	_	2	advmod	_	_
2	gjer	gjere	VERB	verb	Mood=Ind|Tense=Pres|VerbForm=Fin	0	root	_	_
3	eg	eg	PRON	pron	Animacy=Hum|Case=Nom|Person=1|PronType=Prs	2	nsubj	_	_
4	det	det	PRON	pron	Gender=Neut|Person=3|PronType=Prs	2	obj	_	SpaceAfter=No
5	:	$:	PUNCT	clb	_	2	punct	_	_
"""
    file = tmp_path / "ud.conllu"
    file.write_text(text)
    return file


@pytest.fixture
def fake_conll_file(tmp_path):
    file = tmp_path / "input.conllu"
    file.write_text("# sent_id = 1\n1\tDette\t_\t_\t_\t_\t0\troot\t_\t_")
    return file


@pytest.fixture
def tmp_output_dir(tmp_path):
    path = tmp_path / "output"
    path.mkdir()
    return path
