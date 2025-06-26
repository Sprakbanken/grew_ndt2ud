from collections import defaultdict
from pathlib import Path

import pandas as pd

from grew_ndt2ud.src.grew_ndt2ud.parse_conllu import (
    CONLLFIELDS,
    parse_conll_file,
    write_conll,
)

##### CONSTANTS

symbols = ["$", "£", "%", ":(", ":)", "+", "-", "/", ">="]

auxlemmas = [
    "bli",
    "verte",
    "burde",
    "få",
    "ha",
    "kunne",
    "vilje",
    "måtte",
    "skulle",
    "tørre",
    "ville",
    "være",
    "vere",
]


quantifiers = [
    "all",
    "alt",
    "alle",
    "en",
    "ein",
    "et",
    "ei",
    "eit",
    "enhver",
    "einkvar",
    "ethvert",
    "einkvan",
    "hver",
    "hvert",
    "kvar",
    "ingen",
    "noe",
    "noen",
    "nokon",
    "samtlige",
    "samtleg",
    "begge",
]


possessivepronouns = [
    "min",
    "din",
    "sin",
    "hans",
    "hennes",
    "hennar",
    "dens",
    "dets",
    "vår",
    "deres",
]


pron_det_lemma_feats_map = {
    "en": "art",
    "ein": "art",
    "seg": "pers",
    "noen": "ind",
    "noe": "ind",
    "nokon": "ind",
    "endel": "ind",
    "ingen": "negpron|neg",
    "ingenting": "negpron|neg",
    "alle": "tot",
    "all": "tot",
    "hver": "tot",
    "kvar": "tot",
    "enhver": "tot",
    "ethvert": "tot",
    "einkvar": "tot",
    "einkvan": "tot",
    "begge": "tot",
    "samtlige": "tot",
    "samtleg": "tot",
    "selv": "pers",
    "selve": "pers",
    "sjølv": "pers",
    "egen": "pers",
    "eigen": "pers",
    "som": "rel",
}


pron_det_lemma_feats_map.update({posspron: "pers" for posspron in possessivepronouns})


pron_feats = ["pers", "dem", "sp", "res", "art", "ind", "negpron", "tot", "rel"]


verb_feats = ["pres", "pret", "perf-part", "imp", "inf", "pres-part"]


posmap = {
    "adj": "ADJ",
    #    "adv": "ADV",
    "konj": "CCONJ",  # renamed in 2.0
    "interj": "INTJ",
    "inf-merke": "PART",
    "pron": "PRON",
    "<komma>": "PUNCT",
    "<strek>": "PUNCT",
    "<anf>": "PUNCT",
    "<parentes-slutt>": "PUNCT",
    "<parentes-beg>": "PUNCT",
    # "symb": "SYM",
    "ukjent": "X",
    "clb": "PUNCT",
}

featsmap = {
    "1": {"Person": "1"},
    "2": {"Person": "2"},
    "3": {"Person": "3"},
    "<adj>": "_",  # POS = ADJ
    "<adv>": "_",  # POS=ADV
    "<ikke-clb>": "_",  # Not Clause boundary
    "<kolon>": "_",  # Colon, POS=PUNCT
    "<ordenstall>": {"NumType": "Ord"},  # lagt til 2.12
    "<perf-part>": {"VerbForm": "Part"},
    "<pres-part>": {"VerbForm": "Part"},
    "<punkt>": "_",  # tegnsetting, POS=PUNCT
    "<s-verb>": "_",
    "<spm>": "_",  # Spørsmålstegn, POS=PUNCT
    "<utrop>": "_",  #! POS=PUNCT
    "akk": {"Case": "Acc"},
    "appell": "_",  # Common noun, POS=NOUN
    "art": {"PronType": "Art"},
    "be": {"Definite": "Def"},
    "card": {"NumType": "Card"},
    "clb": "_",  # Clause Boundary
    "dem": {"PronType": "Dem"},
    "ent": {"Number": "Sing"},
    "fem": {"Gender": "Fem"},
    "fl": {"Number": "Plur"},
    "fork": {"Abbr": "Yes"},
    "forst": "_",  # eg. selv, egen
    "gen": {"Case": "Gen"},
    "hum": {"Animacy": "Hum"},
    "imp": {"Mood": "Imp", "VerbForm": "Fin"},
    "ind": {"PronType": "Ind"},
    "inf": {"VerbForm": "Inf"},
    "komp": {"Degree": "Cmp"},
    "kvant": "_",  # quantifier (POS=DET)
    "m/f": {"Gender": "Com"},  # New 2.16
    "mask": {"Gender": "Masc"},
    "neg": {"Polarity": "Neg"},
    "negpron": {"PronType": "Neg"},
    "nom": {"Case": "Nom"},
    "nøyt": {"Gender": "Neut"},
    "pass": {"Voice": "Pass"},
    "perf-part": {"VerbForm": "Part"},
    "pers": {"PronType": "Prs"},
    "pos": {"Degree": "Pos"},
    "poss": {"Poss": "Yes"},
    "pres": {"Mood": "Ind", "Tense": "Pres", "VerbForm": "Fin"},
    "pret": {"Mood": "Ind", "Tense": "Past", "VerbForm": "Fin"},
    "prop": "_",  # Egennavn, POS = PROPN
    "refl": {"Reflex": "Yes"},
    "rel": {"PronType": "Rel"},
    "res": {"PronType": "Rcp"},
    "samset": "_",  # ? DEPREL=compound? flat? fixed?
    "sp": {"PronType": "Int"},
    "sup": {"Degree": "Sup"},
    "tot": {"PronType": "Tot"},
    "ub": {"Definite": "Ind"},
    "ubøy": "_",  # Uninflected
    "ufl": "_",  # Incomplete
    "unorm": "_",  # feat Typo?
}

ud_feattypes = [
    "Abbr",
    "Animacy",
    "Case",
    "Definite",
    "Degree",
    "Gender",
    "Mood",
    "NumType",
    "Number",
    "Person",
    "Polarity",
    "Poss",
    "PronType",
    "Reflex",
    "Tense",
    "VerbForm",
    "Voice",
]

### UTILITY FUNCTIONS


def is_ud_feat(feat):
    feattype = feat.split("=")[0]
    return feattype in ud_feattypes


def split_token(line: str) -> list:
    # return line.strip().split('\t')
    return line.rstrip("\n").split("\t")


def is_neg(token):
    lemma = get_field(token, "LEMMA")
    deprel = get_field(token, "DEPREL")
    return (lemma in ["ikke", "ikkje"]) or (lemma == "ingen" and deprel == "DET")


def is_copula(token, deps):
    return get_field(token, "LEMMA") in ("være", "vere") and has_dep_label(
        "SPRED", deps
    )


def has_dep_label(deprel, deps):
    if not deps:
        return False
    labels = [get_field(dep, "DEPREL") for dep in deps]
    return deprel in labels


def field_is_empty(field):
    if isinstance(field, list):
        return (len(field) == 1 and field[0] == "_") or (field == [])
    elif isinstance(field, str):
        return field == "_"


def replace_placeholder(feats: list, addendum: list):
    if field_is_empty(feats):
        return addendum if not field_is_empty(addendum) else ["_"]
    feats.extend(addendum)
    return list(set(feats))


def split_batch_samples(filename, sample_size: int = 200000):
    """Split data into batches to upload to Arborator Grew."""
    filepath = Path(filename)
    lines = filepath.read_text().splitlines()
    length = len(lines)

    def split_samples(start):
        remaining_length = length - start
        end = start + sample_size if sample_size < remaining_length else length

        rev = lines[:end]
        rev.reverse()
        last_sent_rev_idx = rev.index("")
        end -= last_sent_rev_idx

        sample = lines[start:end]
        sample.pop()
        return end, sample

    # Number of samples in the data, given the sample size
    iterations = (length // sample_size) + int(length % sample_size > 0)

    idx = 0
    for i in range(iterations):
        idx, sample = split_samples(idx)
        path = filepath.parent / f"sample{i + 1}_{filepath.name}"
        with open(path, "w+") as sf:
            for line in sample:
                sf.write(line + "\n")


########## NEW CONVERSION FUNCTIONS ######

# for UD v2.12 (2023)
# Author Ingerid L. Dale

# Utils


def overlaps(actual_values, qualifying_values):
    return any(feat in qualifying_values for feat in actual_values)


# Konverter POS-taggene


def get_dependents(sentence, token):
    return [
        token_i for token_i in sentence if get_field(token, "ID") == token_i.get("HEAD")
    ]  # token.get("ID") != token_i.get("ID") ]


def get_labels(tokens):
    return [get_field(t, "DEPREL") for t in tokens]


def get_field(token, field):
    field = field.upper()
    if isinstance(token, dict):
        return token.get(field)
    elif isinstance(token, pd.DataFrame):
        return token[field]
    elif isinstance(token, list):
        return token[CONLLFIELDS.index(field)]


def convert_pos(token, sentence):
    pos = get_field(token, "UPOS")
    lemma = get_field(token, "LEMMA")
    feats = get_field(token, "FEATS").split("|")

    # direct mapping
    def convert_verb_pos():
        deps = get_dependents(sentence, token)
        labels = get_labels(deps) if deps else []

        if (
            "INFV" in labels and lemma in auxlemmas
            # token is a modal auxiliary verb
        ) or (
            "SPRED" in labels and lemma in ("være", "vere")
            # token is a copular verb
        ):
            return "AUX"
        return "VERB"

    def convert_det_pos():
        if "poss" in feats:
            return "PRON"
        if "romertall" in feats:
            return "NUM"
        if "kvant" in feats:
            return "DET" if lemma in quantifiers else "NUM"
        return "DET"

    def convert_prep_pos():
        if lemma == "der" and get_field(token, "DEPREL") in ["FSUBJ", "FOBJ"]:
            return "PRON"
        elif lemma in ["her", "her", "der", "herfra", "derfra", "hit", "dit"]:
            return "ADV"
        return "ADP"

    # special cases
    pos_conversion = {
        "subst": "PROPN" if "prop" in feats else "NOUN",
        "symb": "PUNCT" if lemma == "*" else "SYM",
        "verb": convert_verb_pos(),  #'VERB' or 'AUX',
        "det": convert_det_pos(),  #'DET', 'PRON', 'NUM'
        "adj": "ADJ",
        "adv": "PART" if lemma in ["ikke", "ikkje", "ei"] else "ADV",  #'ADV',
        "clb": "PUNCT",
        "prep": convert_prep_pos(),  #'ADP',"PRON", 'ADV'
        "pron": "PRON",
        "<komma>": "PUNCT",
        "konj": "CCONJ",
        "inf-merke": "PART",
        "<anf>": "PUNCT",
        "sbu": "SCONJ",
        "<strek>": "PUNCT",
        "ukjent": "X",  # feat: Foreign=Yes
        "<parentes-beg>": "PUNCT",
        "<parentes-slutt>": "PUNCT",
        "interj": "INTJ",
    }
    return pos_conversion.get(pos, pos)


# Konverter feats


def add_feats(token):
    lemma = get_field(token, "LEMMA")
    pos = get_field(token, "UPOS")
    feats = get_field(token, "FEATS").split("|")  # turn feats into a list
    new_feats = []

    if pos == "NUM":
        new_feats.append("card")
    if is_neg(token) and pos != "X":
        new_feats.append("neg")
    if pos == "PRON" or pos == "DET":
        if lemma not in pron_det_lemma_feats_map and overlaps(feats, pron_feats):
            return feats
        new_feats.append(pron_det_lemma_feats_map.get(lemma, "pers"))
    if pos == "VERB" or pos == "AUX":
        if overlaps(feats, verb_feats):
            return feats
        new_feats.append("pres")
    return replace_placeholder(feats, new_feats)


def convert_feats(token):
    feats = add_feats(token)
    mapped_feats = map_feats(feats)
    formatted = "|".join(sorted(mapped_feats, key=str.lower))
    return formatted if formatted else "_"


def map_feats(feats):
    newfeats = defaultdict(set)
    mapped = (featsmap.get(feat, "_") for feat in feats)
    for feat in mapped:
        if not isinstance(feat, dict):
            continue
        for feattype, val in feat.items():
            newfeats[feattype].add(val)
    formatted = [format_ud_feat(*feat) for feat in newfeats.items()]
    return formatted


def format_ud_feat(feat_type, feat_val):
    value = ",".join(sorted(feat_val, key=str.lower))
    return f"{feat_type}={value}"


# Konverter POS og  morfologiske trekk fra NDT til UD


def convert_morphology(data):
    conll_data = data.copy()
    for s in conll_data.get("sentences"):
        sentence = s.get("tokens")
        converted = []
        for token in sentence:
            token["UPOS"] = convert_pos(token, sentence)
            if not all(is_ud_feat(f) for f in token["FEATS"].split("|")):
                token["FEATS"] = convert_feats(token)
            converted.append(token)
        s["tokens"] = converted
    return conll_data


def process_file(filename, outputfile, add_comments):
    # Konverter alle splittene av retokenisert ndt data
    fpath = Path(filename)
    data = parse_conll_file(fpath)
    morphdata = convert_morphology(data)
    if outputfile is None:
        outputfile = fpath.parent / f"{fpath.stem}_udmorph{fpath.suffix}"
    write_conll(morphdata, Path(outputfile), add_comments=add_comments)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-rc", "--remove_comments", action="store_false")
    parser.add_argument("-f", "--file")
    parser.add_argument("-o", "--outputfile", default=None)
    args = parser.parse_args()

    process_file(args.file, args.outputfile, args.remove_comments)
