"""Script to parse, filter and write conllu-files for use with MaltEval.

Module copied from https://github.com/Sprakbanken/trebankdatabase/blob/master/utils.py

Changes from the original utils functions:
- "_" does NOT get swapped out with None.
- Extra regex patterns to match metadata comment lines

Below are additional functions to filter sentences on ids, load the parsed conll into a dataframe,
write conllu files with selected metadata (sent_id, text)
"""

import re
from csv import QUOTE_NONE
from pathlib import Path
from typing import Generator

import pandas as pd

CONLLFIELDS = [
    "ID",
    "FORM",
    "LEMMA",
    "UPOS",
    "XPOS",
    "FEATS",
    "HEAD",
    "DEPREL",
    "DEPS",
    "MISC",
]


# Regular expressions for reading conll lines

COMMENTPATTERN = re.compile(r"^# (.+?) = (.+?)$")
NEWPARDOCPATTERN = re.compile(r"^# (newpar|newdoc)(?: id = )?(.*)?$")
EMPTYLINEPATTERN = re.compile(r"^$")
TOKENLINEPATTERN = re.compile(
    r"^(?P<index>\d+)\t(?P<form>.+?)\t(?P<lemma>.*?)\t(?P<UPOS>.+?)\t(?P<xpos>.*?)\t(?P<feats>.*?)\t(?P<head>\d+?)\s(?P<DEPREL>.+?)\t(?P<extra>.*?)\t(?P<misc>.*?)$"
)
DIALECTPATTERN = re.compile(r"^# dialect:\s*(.*)$")


def validate_conll_lines(lines: list) -> list:
    """Check a list of lines to see if they are valid lines of a conll file
    if all lines are valid, the lines are returned. Else, an error is raised
    and invalid lines are printed.

    Parameter
    ----------
    lines: list
        a list of lines, e.g., from a conll file or from a scrupt generating
        conll-formated data
    """
    invalid_lines = []
    for i, line in enumerate(lines):
        validline = any(
            pattern.match(line)
            for pattern in [
                COMMENTPATTERN,
                NEWPARDOCPATTERN,
                EMPTYLINEPATTERN,
                TOKENLINEPATTERN,
                DIALECTPATTERN,
            ]
        )
        if not validline:
            invalid_lines.append(f"line: {i}, text: {line}")
    if invalid_lines:
        print("Error: There are invalid line(s):")
        for invalidline in invalid_lines:
            print(invalidline.strip())
    return lines


def parse_line(conll_line: str) -> dict:
    """Parses a string containing a valid conll line and returns a dict
    with the UD field names as keys and values from the split string.
    ID and HEAD values are integers.

    Parameter
    ----------
    conll_line: str
        a valid conll-formatted line
    """

    vals = conll_line.strip().split("\t")
    token = dict(zip(CONLLFIELDS, vals))
    parsed = token.copy()

    for k, v in token.items():
        if k in ["ID", "HEAD"]:
            parsed[k] = int(v)  # type: ignore
        if (v is None) or (v == ""):
            parsed[k] = "_"

    return parsed


def parse_conll_file(filepath: Path) -> dict:
    """Opens a conll file and returns a dict representation of
    the content of that file. On the top level, there is a key
    "file" with the filename sting, as well as "sentences",
    taking a list of sentence dicts as a value. For each sentence
    comments of type "# feature = value" is converted to a key-value
    pair in the sentence dict, and "# newpar" is converted to ""newpar": True"

    Parameter
    ----------
    filepath: pathlib.Path
        a conll file
    """

    conlldict = {"file": filepath.name, "sentences": []}
    sentdict = {"tokens": []}
    lines = validate_conll_lines(filereadlines(filepath))
    for line in lines:
        if EMPTYLINEPATTERN.match(line):
            if not sentdict["tokens"]:
                pass
            conlldict["sentences"].append(sentdict)
            sentdict = {"tokens": []}
        elif matchobj := NEWPARDOCPATTERN.match(line):
            metadata = matchobj.group(1)
            sentdict[metadata] = True  # type: ignore
        elif matchobj := COMMENTPATTERN.match(line):
            metadata = matchobj.group(1)
            if metadata == "ud_id" or metadata == "id":
                metadata = "sent_id"
            sentdict[metadata] = matchobj.group(2)  # type: ignore

        elif TOKENLINEPATTERN.match(line):
            sentdict["tokens"].append(parse_line(line))
    return conlldict


### End of copied module ###


def filereadlines(id_file):
    return Path(id_file).read_text().splitlines()


# Skriv CONLLU-filer med eller uten kommentarlinjer
def add_commentlines(sentence: dict) -> Generator:
    """Format comment lines with sentence metadata"""
    for meta, value in sentence.items():
        if meta in ("newpar", "newdoc"):
            yield f"# {meta}\n"
        elif meta in ("sent_id", "text", "dialect", "newpar id", "newdoc id"):
            yield f"# {meta} = {value}\n"


def write_conll(data: dict, conllu_filepath: str | Path, drop_comments: bool = False):
    """Format a dict with treebank data to conllu strings."""

    def format_conllu_lines(sentences: list) -> Generator:
        for sentence in sentences:
            if not drop_comments:
                yield from add_commentlines(sentence)
            for token in sentence.get("tokens"):
                yield "\t".join(map(str, token.values())) + "\n"
            yield "\n"

    output_data = format_conllu_lines(data["sentences"])
    with open(conllu_filepath, "w+", encoding="utf-8") as fp:
        fp.writelines(output_data)


def load_conll_to_df(conll: dict) -> pd.DataFrame:
    """Load a dictionary with conlldata into a pandas dataframe"""
    dfs = []
    for idx, sentence in enumerate(conll["sentences"]):
        sent_df = pd.DataFrame(sentence.get("tokens"))
        for col in sentence.keys():
            if col == "tokens":
                continue
            sent_df[col] = sentence.get(col)
        sent_df["idx"] = idx
        dfs.append(sent_df)

    return pd.concat(dfs, ignore_index=True).fillna(False)


def get_conll_tsv(df: pd.DataFrame) -> str:
    """Turn a dataframe with conll data into a tsv-formatted string"""
    return df[CONLLFIELDS].to_csv(
        sep="\t",
        header=False,
        index=False,
        quoting=QUOTE_NONE,
        quotechar="",
        escapechar="\\",
        na_rep="_",
    )


def df_to_conll(totaldf: pd.DataFrame, drop_comments: bool = False):
    """Produce conllu string from a pandas dataframe."""
    gb = totaldf.groupby("idx")
    mystring = ""
    ids = gb.groups.keys()
    for id in ids:
        df = gb.get_group(id).copy()
        if not drop_comments:
            for line in add_commentlines(df.iloc[0].to_dict()):
                mystring += line
        mystring += get_conll_tsv(df)
        mystring += "\n"
    return mystring
