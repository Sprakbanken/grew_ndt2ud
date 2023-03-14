"""Script to parse, filter and write conllu-files for use with MaltEval.

The following regex patterns and functions are fetched from https://github.com/peresolb/trebankdatabase/blob/master/utils.py
The only change to the original utils module is that "_" does NOT get swapped out with None.

Below is a new function to filter sentences on ids.
"""

from pathlib import Path
import re


# Regular expressions for reading conll lines

COMMENTPATTERN = re.compile(r'^# (.+?) = (.+?)\n')
NEWPARPATTERN = re.compile(r'^# newpar\n')
EMPTYLINEPATTERN = re.compile(r'^\n')
TOKENLINEPATTERN = re.compile(r'^\d+\t([^\s]+?\t){8}[^\s]+?\n')

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
        validline = False
        for pattern in [
                        COMMENTPATTERN,
                        NEWPARPATTERN,
                        EMPTYLINEPATTERN,
                        TOKENLINEPATTERN
                        ]:
            if pattern.match(l):
                validline = True
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
    conlldict = {k: v for k, v in zip(CONLLFIELDS, vals)}

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
    with filepath.open(mode='r') as f:
        lines = validate_conll_lines(f.readlines())
        for line in lines:
            if EMPTYLINEPATTERN.match(line):
                if not sentdict['tokens']:
                    pass
                conlldict['sentences'].append(sentdict)
                sentdict = {'tokens': []}
            elif NEWPARPATTERN.match(line):
                sentdict['newpar'] = True
            elif COMMENTPATTERN.match(line):
                matchobj = COMMENTPATTERN.match(line)
                sentdict[matchobj.group(1)] = matchobj.group(2)
            elif TOKENLINEPATTERN.match(line):
                sentdict['tokens'].append(parse_line(line))
    return conlldict


### End of copied module ###

# Filter data by ids

def extract_partition(sentences, id_list):
    partition = [sent for sent in sentences if sent.get("sent_id") in id_list]
    return sorted(partition, key=lambda x: x.get("sent_id"))


def get_ids(id_file):
    return Path(id_file).read_text().split("\n")


def format_conll_line(token_dict):
    return "\t".join([str(t) for t in token_dict.values()])


def iterate_conll_data_no_hash(data):
    for sentence in data:
        for token in sentence.get("tokens"):
            yield format_conll_line(token) + "\n"
        yield "\n"
    return "\n"


def write_conll(data, output_file, suffix=None):
    output_file = output_file.parent / f"{output_file.stem}{suffix if suffix else ''}.conllu"
    print(f"Write conll data to {output_file}")
    with open(output_file, "w+", encoding="utf-8") as fp:
        fp.writelines(iterate_conll_data_no_hash(data))


def partition_by_sent_ids(conll_file, id_files):
    fpath = Path(conll_file)
    sentences = parse_conll_file(fpath).get("sentences")

    for id_file in id_files:
        part = re.match(r".*[_-](\w+)_ids.txt", id_file).group(1)
        print(f"Extract partition '{part}' from {fpath.name}")
        ids = get_ids(id_file)
        partition = extract_partition(sentences, ids)
        write_conll(partition, fpath, suffix=f"_{part}_uten_hash")


def remove_comments(conll_file):
    fpath = Path(conll_file)
    conll_data = parse_conll_file(fpath).get("sentences")
    write_conll(conll_data, fpath, suffix="_uten_hash")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infiles", nargs="*")
    parser.add_argument("-f", "--filter_ids", nargs="*")
    args = parser.parse_args()

    for datafile in args.infiles:
        print(f"Processing file: {datafile}")
        if args.filter_ids is not None:
            partition_by_sent_ids(datafile, args.filter_ids)
        else:
            remove_comments(datafile)

    print("Done.")
