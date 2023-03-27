"""Script to parse, filter and write conllu-files for use with MaltEval.

Module copied from https://github.com/Sprakbanken/trebankdatabase/blob/master/utils.py

Changes from the original utils functions:
- "_" does NOT get swapped out with None.
- Extra regex patterns to match "newpar" and "newdoc" comment lines

Below are additional functions to filter sentences on ids, load the parsed conll into a dataframe,
write conllu files with selected metadata (sent_id, text)
"""

from pathlib import Path
import re
import sys

# Conll fields

CONLLFIELDS = [
                'ID',
                'FORM',
                'LEMMA',
                'UPOS',
                'XPOS',
                'FEATS',
                'HEAD',
                'DEPREL',
                'DEPS',
                'MISC'
            ]


# Regular expressions for reading conll lines

COMMENTPATTERN = re.compile(r'^# (.+?) = (.+?)$')
NEWPARDOCPATTERN = re.compile(r'^# (newpar|newdoc)(?: id = )?(.*)?$')
EMPTYLINEPATTERN = re.compile(r'^$')
TOKENLINEPATTERN = re.compile(r'^\d+\t([^\s]+?\t){8}[^\s]+?$')


# Functions


def validate_conll_lines(lines: list) -> list:
    '''Check a list of lines to see if they are valid lines of a conll file
    if all lines are valid, the lines are returned. Else, an error is raised
    and invalid lines are printed.

    Parameter
    ----------
    lines: list
        a list of lines, e.g., from a conll file or from a scrupt generating
        conll-formated data
    '''
    invalid_lines = []
    validlines = True
    for i, l in enumerate(lines):
        validline = any(
            pattern.match(l) for pattern in [
                COMMENTPATTERN,
                NEWPARDOCPATTERN,
                EMPTYLINEPATTERN,
                TOKENLINEPATTERN
            ])
        if not validline:
            validlines = False
            invalid_lines.append(f'line: {i}, text: {l}')
    try:
        assert validlines
        return lines
    except AssertionError:
        print('Error: There are invalid line(s):')
        for invalidline in invalid_lines:
            print(invalidline.strip())


def parse_line(conline: str) -> dict:
    '''Parses a string containing a valid conll line and returns a dict
    with the UD field names as keys and values from the split string.
    ID and HEAD values are integers and '_' is replaced with None

    Parameter
    ----------
    conline: str
        a valid conll-formatted line
    '''

    vals = conline.strip().split('\t')
    conlldict = dict(zip(CONLLFIELDS, vals))

    for k, v in conlldict.items():
        if k in ['ID', 'HEAD']:
            conlldict[k] = int(v)

    return conlldict


def parse_conll_file(filepath: Path) -> dict:
    '''Opens a conll file and returns a dict representation of
    the content of that file. On the top level, there is a key
    "file" with the filename sting, as well as "sentences",
    taking a list of sentence dicts as a value. For each sentence
    comments of type "# feature = value" is converted to a key-value
    pair in the sentence dict, and "# newpar" is converted to ""newpar": True"

    Parameter
    ----------
    filepath: pathlib.Path
        a conll file
    '''

    conlldict = {'file': filepath.name, 'sentences': []}
    sentdict = {'tokens': []}
    lines = validate_conll_lines(filepath.read_text().splitlines())
    for line in lines:
        if EMPTYLINEPATTERN.match(line):
            if not sentdict['tokens']:
                pass
            conlldict['sentences'].append(sentdict)
            sentdict = {'tokens': []}
        elif (matchobj := NEWPARDOCPATTERN.match(line)):
            sentdict[matchobj.group(1)] = True
        elif (matchobj := COMMENTPATTERN.match(line)):
            metadata = matchobj.group(1)
            if metadata == "ud_id":
                metadata = "sent_id"
            sentdict[metadata] = matchobj.group(2)

        elif TOKENLINEPATTERN.match(line):
            sentdict['tokens'].append(parse_line(line))
    return conlldict


### End of copied module ###


def filereadlines(id_file):
    return Path(id_file).read_text().splitlines()


# Filter data by ids

def extract_partition(data, id_list):
    partition = [sent for sent in data.get("sentences") if sent.get("sent_id") in id_list]
    return sorted(partition, key=lambda x: x.get("sent_id"))


def add_commentlines(datadict, metadatafields):
    for meta in metadatafields:
        value = datadict.get(meta)
        if not value:
            continue
        yield f"# {meta} = {value}\n"

#Skriv CONLLU-filer med og uten kommentarlinjer

def iterate_conll_data_dict(data, add_comments=False):
    for sentence in data.get("sentences"):
        if add_comments:
            # Can be 'sent_id', 'text', 'newpar' or 'newpar id', 'newdoc' or 'newdoc id'
            for line in add_commentlines(sentence, ["sent_id", "text"]):
                yield line
        for token in sentence.get("tokens"):
            yield "\t".join(map(str, token.values())) + "\n"
        yield "\n"
    return "\n"


def write_conll(data, path: Path, add_comments=False):
    print(f"Write conll data to {path.name}")
    output_data = iterate_conll_data_dict(data, add_comments=add_comments)
    with open(path, "w+", encoding="utf-8") as fp:
        fp.writelines(output_data)


def partition_by_sent_ids(data, id_files):

    parts = {}
    for id_file in id_files:
        part = re.match(r".*[_-](\w+)_ids.txt", id_file).group(1)
        print(f"Extract partition '{part}' from {fpath.name}")
        ids = filereadlines(id_file)
        parts[part] = extract_partition(data, ids)
    return parts


if __name__ == "__main__":

    for datafile in sys.argv[1:]:
        print(f"Processing file: {datafile}")
        fpath = Path(datafile)
        output = fpath.parent / f"{fpath.stem}_OUTPUT{fpath.suffix}"
        write_conll(parse_conll_file(fpath), output, add_comments=False)


    print("Done.")
