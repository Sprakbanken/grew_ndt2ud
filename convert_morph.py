
import re
import sys

from collections import defaultdict
from pathlib import Path


##### CONSTANTS
conll_field_index = {
    "id": 0,
    "form": 1,
    "lemma": 2,
    "pos": 3,
    "cpos": 4,
    "feats": 5,
    "head": 6,
    "deprel": 7,
    "deps": 8,
    "misc": 9,
}

auxlemmas = ["bli", "burde", "få", "ha", "kunne",
             "måtte", "skulle", "tørre", "ville", "være"]

qdet = ["all", "alt", "alle", "en", "et", "ei", "enhver", "ethvert",
        "hver", "hvert", "ingen", "noe", "noen", "samtlige", "begge"]

possessivepronouns = ["min", "din", "sin", "hans",
                      "hennes", "dens", "dets", "vår", "deres"]

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
    "mask": {"Gender": "Masc"},
    "fem": {"Gender": "Fem"},
    "nøyt": {"Gender": "Neut"},
    "ent": {"Number": "Sing"},
    "fl": {"Number": "Plur"},
    "be": {"Definite": "Def"},
    "ub": {"Definite": "Ind"},
    "pres": {"Mood": "Ind", "Tense": "Pres", "VerbForm": "Fin"},
    "pret": {"Mood": "Ind", "Tense": "Past", "VerbForm": "Fin"},
    "perf-part": {"VerbForm": "Part"},
    "imp": {"Mood": "Imp", "VerbForm": "Fin"},
    "pass": {"Voice": "Pass"},
    "inf": {"VerbForm": "Inf"},
    "<perf-part>": {"VerbForm": "Part"},
    "<pres-part>": {"VerbForm": "Part"},
    "1": {"Person": "1"},
    "2": {"Person": "2"},
    "3": {"Person": "3"},
    "nom": {"Case": "Nom"},
    "akk": {"Case": "Acc"},
    "gen": {"Case": "Gen"},  # v2.0
    "pos": {"Degree": "Pos"},
    "komp": {"Degree": "Cmp"},
    "sup": {"Degree": "Sup"},
    "hum": {"Animacy": "Hum"},  # v
    "pers": {"PronType": "Prs"},
    "dem": {"PronType": "Dem"},
    "sp": {"PronType": "Int"},
    "res": {"PronType": "Rcp"},
    "art": {"PronType": "Art"},
    "ind": {"PronType": "Ind"},
    "negpron": {"PronType": "Neg"},
    "neg": {"Polarity": "Neg"},
    "tot": {"PronType": "Tot"},
    "rel": {"PronType": "Rel"},
    "poss": {"Poss": "Yes"},
    "refl": {"Reflex": "Yes"},
    "card": {"NumType": "Card"},
    "fork": {"Abbr": "Yes"}  # v2.0
}

### UTILITY FUNCTIONS


def split_token(line: str) -> list:
    return line.rstrip("\n").split("\t")


def is_neg(token):
    lemma = token.get("lemma")
    deprel = token.get("deprel")
    return (lemma == "ikke" or (lemma == "ingen" and deprel == "DET"))


def is_copula(token, deps):
    return (get_lemma(token) == "være" and has_dep_label("SPRED", deps))


def has_dep_label(deprel, deps):
    if deps:
        labels = map(get_deprel, deps)
        return (deprel in labels)
    return False


def get_lemma(fields):
    """
    return the lemma
    """
    return fields[2]


def get_deprel(fields):
    return fields[7]

def get_head(fields):
    """
    return the head
    """
    return int(fields[6])

def get_fields(token, field=None):
    token[0] = int(token[0])
    token[6] = int(token[6])
    token_fields = {field: token[idx] for field,
                    idx in conll_field_index.items() if idx < len(token)}
    if field is None:
        return token_fields
    return token_fields.get(field)


def field_is_empty(field):
    if isinstance(field, list):
        return len(field) == 1 and field[0] == "_"
    elif isinstance(field, str):
        return field == "_"


def replace_placeholder(feats, addendum):
    if field_is_empty(feats):
        return [addendum]
    else:
        feats.append(addendum)
        return feats

def iterate_sentences(filename):
    with open(filename, 'r') as fp:
        file_data = fp.readlines()

    sentence = []
    for line in file_data:
        if line.startswith("#"):
            continue
        elif (line != "\n"):
            sentence.append(split_token(line))
        elif line == "\n":
            yield sentence
            sentence = []


def format_tab_separated(token):
    return "\t".join(map(str, token))


def write_conll_file(filename, sentences):
    with open(filename, "w+") as fp:
        for sentence in sentences:
            for token_data in sentence:
                fp.write(format_tab_separated(token_data) + "\n")
            fp.write("\n")


def create_filepaths(input_filename: str, output_suffix="udfeats-pos"):
    filename = Path(input_filename)

    output_dir = filename.parents[0] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"{filename.stem}_{output_suffix}{filename.suffix}"
    output_path = output_dir / output_filename

    return filename, output_path


### PROCESSING FUNCTIONS

def process(filename: Path, outputfile: Path):
    """Convert a CONLL file from the NDT format to the UD format.

    Default output filename is {path/to/input/filename}_UDfeats.conllu
    """
    conll_data = iterate_sentences(filename)
    sentences = [list(convert_morphological_analysis(sentence))
                 for sentence in conll_data]
    return sentences


def batch_samples_arborator(filename, sample_size: int = 200000):
    filepath = Path(filename)
    lines = filepath.read_text().split("\n")
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
        path = filepath.parent / f"sample{i+1}_{filepath.name}"
        with open(path, "w+") as sf:
            for line in sample:
                sf.write(line + "\n")


def convert_morphological_analysis(sentence):
    idx = conll_field_index

    for token in sentence:
        try:
            token[idx["pos"]] = convert_pos(token, sentence)
            token[idx["cpos"]] = "_"
            token[idx["feats"]] = convert_feats(token)
            yield token
        except ValueError:
            print("Skipping token that raises value errror:", token)
            continue
        except Exception as e:
            print(token)
            raise e


def convert_feats(token):
    feats = add_feats(token)
    newfeats = defaultdict(list)

    for feat in feats:
        featsmapping = featsmap.get(feat, "_")
        if featsmapping == feat == "_":
            return feat
        elif isinstance(featsmapping, str) and feat != "_":
            newfeats[feat].append(feat)
        elif isinstance(featsmapping, dict):
            for (feattype, val) in featsmapping.items():
                newfeats[feattype].append(val)

    sorted_feats = sorted(newfeats.items(), key=lambda k: k[0].lower())
    formatted = []

    for feat_cat, feat_val in sorted_feats:
        value = ",".join(sorted(feat_val, key=str.lower)) if len(
            feat_val) > 1 else feat_val[0]
        if feat_cat == value:
            continue
        feat = f"{feat_cat}={value}"
        formatted.append(feat if feat != "=" else "_")

    return "|".join(formatted)


def add_feats(token):
    token = get_fields(token)
    lemma = token.get("lemma")
    pos = token.get("cpos")
    feats = token.get("feats").split("|")  # turn feats into a list

    if pos == "PRON" or pos == "DET":
        pron_det_lemma_feats_map = {
            "en": "art",
            "seg": "pers",
            "noen": "ind",
            "noe": "ind",
            "endel": "ind",
            "ingen": "negpron|neg",
            "ingenting": "negpron|neg",
            "alle": "tot",
            "all": "tot",
            "hver": "tot",
            "enhver": "tot",
            "begge": "tot",
            "samtlige": "tot",
            "selv": "pers",
            "selve": "pers",
            "sjølv": "pers",
            "egen": "pers",
            "som": "rel",
        }
        pron_det_lemma_feats_map.update(
            {posspron: "pers" for posspron in possessivepronouns})

        to_add = pron_det_lemma_feats_map.get(lemma, "")

        if to_add == "":
            pron_feats = ['pers', 'dem', 'sp', 'res',
                          'art', 'ind', 'negpron', 'tot', 'rel']
            if any(feat in pron_feats for feat in feats):
                return feats
            else:
                to_add = "pers"
        return replace_placeholder(feats, to_add)

    elif pos == "NUM":
        to_add = "card"
        return replace_placeholder(feats, to_add)

    elif pos == "VERB" or pos == "AUX":
        verb_feats = ['pres', 'pret', 'perf-part', 'imp', 'inf', 'pres-part']

        if any(feat in verb_feats for feat in feats):
            return feats
        else:
            to_add = "pres"
        return replace_placeholder(feats, to_add)

    elif is_neg(token):
        to_add = "neg"
        return replace_placeholder(feats, to_add)

    return feats


def convert_pos(token, sentence):
    fields = get_fields(token)
    pos = fields.get("pos")
    lemma = fields.get("lemma")
    deprel = fields.get("deprel")
    form = fields.get("form")
    feats = fields.get("feats").split("|")
    token_id = fields.get("id")

    # direct mapping
    if pos in posmap:
        return posmap[pos]

    # special cases
    elif pos == "sbu":
        return "PRON" if form == "som" else "SCONJ"

    elif pos == "subst":
        return "PROPN" if "prop" in feats else "NOUN"

    elif pos == "symb":
        return "PUNCT" if lemma in ["$/", "*"] else "SYM"

    elif pos == "verb":
        deps = dependents(sentence, token_id)
        labels = map(get_deprel, deps) if deps else []
        return "AUX" if ("INFV" in labels and lemma in auxlemmas) or is_copula(token, deps) else "VERB"

    elif pos == "det":
        if "kvant" in feats:
            return "DET" if lemma in qdet else "NUM"
        elif "romertall" in feats:
            return "NUM"
        elif "poss" in feats:
            return "PRON"
        else:
            return "DET"

    elif pos == "prep":
        prep_lemma_list = ['her', 'her', 'der',
                           'herfra', 'derfra', 'hit', 'dit']
        prep_dep_list = ["FSUBJ", "FOBJ", "expl"]
        if lemma == "der" and deprel in prep_dep_list:
            return "PRON"
        elif lemma in prep_lemma_list:
            return "ADV"
        else:
            return "ADP"

    elif pos == "adv":
        return "PART" if lemma in ["ikke", "ei"] else "ADV"
    print("Could not convert POS-tag", pos)
    return pos


def dependents(sentence, target_head):
    dependents = []

    for current_id in range(1, len(sentence)):
        if target_head != current_id:
            current_fields = sentence[current_id - 1]
            current_head_id = get_head(current_fields)

            if target_head == current_head_id:
                dependents.append(current_fields)

    return dependents

if __name__ == "__main__":

    print("Konverterer morfologiske trekk og POS-tag")
    for filename in sys.argv[1:]:
        infile, outfile = create_filepaths(filename, output_suffix="udfeatspos")
        converted_data = process(infile, outfile)
        print(outfile)
        write_conll_file(outfile, converted_data)
