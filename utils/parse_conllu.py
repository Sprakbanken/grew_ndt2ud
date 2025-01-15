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
import pandas as pd
from csv import QUOTE_NONE


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
    for i, line in enumerate(lines):
        validline = any(
            pattern.match(line) for pattern in [
                COMMENTPATTERN,
                NEWPARDOCPATTERN,
                EMPTYLINEPATTERN,
                TOKENLINEPATTERN
            ])
        if not validline:
            validlines = False
            invalid_lines.append(f'line: {i}, text: {line}')
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
    lines = validate_conll_lines(filereadlines(filepath))
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


def fetch_ids(datafile):
    for line in filereadlines(datafile):
        if (matchobj := COMMENTPATTERN.match(line)) and matchobj.group(1) in ["ud_id","sent_id"]:
            yield matchobj.group(2)


def extract_partition(data, id_list):
    partition = [sent for sent in data.get("sentences") if sent.get("sent_id") in id_list]
    return sorted(partition, key=lambda x: x.get("sent_id"))


def gather_partition_idlists():
    partitions = {
        "test" :  Path("data/ndt_nb_test.conllu"),
        "dev" : Path("data/ndt_nb_dev.conllu"),
        "train" : Path("data/ndt_nb_train.conllu"),
    }

    for part, part_data in partitions.items():
        part_ids = list(fetch_ids(part_data))
        Path(f"data/{part}_ids.txt").write_text("\n".join(part_ids))



def partition_by_sent_ids(data, id_files):
    parts = {}
    for id_file in id_files:
        part = re.match(r".*[_-]?(\w+)_ids.txt", id_file).group(1)
        print(f"Extract partition '{part}' from data")
        ids = filereadlines(id_file)
        parts[part] = extract_partition(data, ids)
    return parts


#Skriv CONLLU-filer med og uten kommentarlinjer

def add_commentlines(datadict, metadatafields):
    for meta in metadatafields:
        value = datadict.get(meta)
        if not value:
            continue
        yield f"# {meta}\n" if meta in ["newpar", "newdoc"] else f"# {meta} = {value}\n"


def iterate_conll_data_dict(data, add_comments=False):
    for sentence in data.get("sentences"):
        if add_comments:
            # Can be 'sent_id', 'text', 'newpar' or 'newpar id', 'newdoc' or 'newdoc id'
            for line in add_commentlines(sentence,  ["newpar", "sent_id", "text"]):
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


def load_conll_to_df(conlldict):
    dfs =[]
    for idx, sentence in enumerate(conlldict.get("sentences")):
        sent_df = pd.DataFrame(sentence.get("tokens"))
        for col in sentence.keys():
            if col == "tokens":
                continue
            sent_df[col] = sentence.get(col)
        sent_df["idx"] = idx
        dfs.append(sent_df)

    return pd.concat(dfs, ignore_index=True).fillna(False)


def get_conll_csv(df):
    return df[CONLLFIELDS].to_csv(
        sep='\t', header=False, index=False,  quoting=QUOTE_NONE,
        quotechar="", escapechar="\\", na_rep="_")


def write_df_to_conll(totaldf, path= None, add_comments=False):
    """Produce conllu string from a pandas dataframe."""
    gb = totaldf.groupby("idx")
    mystring = ""
    ids = gb.groups.keys()
    for id in ids:
        df = gb.get_group(id).copy()
        if add_comments:
            for line in add_commentlines(df.iloc[0], ["newpar", "sent_id", "text"]):
                mystring += line
        mystring += get_conll_csv(df)
        mystring += "\n"
    if path is not None:
        with Path(path).open(mode="w") as filepath:
            filepath.write(mystring)
    return mystring


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-rc", "--remove_comments", action="store_false")
    parser.add_argument("-f", "--file", action="extend", nargs="+", type=str)
    parser.add_argument("-o", "--outputfile",  type=str, required=False)
    args = parser.parse_args()

    for filename in args.file:
        outfile = args.outputfile if args.outputfile is not None else filename
        write_conll(parse_conll_file(Path(filename)), Path(outfile), add_comments=args.remove_comments)

    print("Done.")
