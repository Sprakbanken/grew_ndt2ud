# %%
import logging
import re
from pathlib import Path

# %%
import grewpy
import pandas as pd
from udapi import Document
from udapi.block.ud.fixchain import FixChain
from udapi.block.ud.fixleaf import FixLeaf
from udapi.block.ud.fixmultisubjects import FixMultiSubjects
from udapi.block.ud.fixpunct import FixPunct
from udapi.block.ud.fixrightheaded import FixRightheaded
from udapi.block.ud.setspaceafterfromtext import SetSpaceAfterFromText
from udapi.block.util.normalize import Normalize


def set_spaceafter_from_text(graph: grewpy.Graph):
    """Implementation of udapi's SetSpaceAfterFromText Block with grewpy.Graph instead"""
    text = graph.meta["text"]
    if text is None or not text:
        raise ValueError("Tree %s has no text: " % graph.meta["sent_id"])

    for node_id in graph:
        if node_id == "0":
            continue
        node = graph[node_id]
        if text.startswith(node["form"]):
            text = text[len(node["form"]) :]
            if not text or text[0].isspace():
                if "SpaceAfter" in node:
                    del node["SpaceAfter"]
                text = text.lstrip()
            else:
                node["SpaceAfter"] = "No"
        else:
            logging.warning('Node %s does not match text "%s"', node, text[:20])
            return
    if text:
        logging.warning('Extra text "%s" in tree %s', text, graph.meta["sent_id"])
    return graph


def udapi_fixes(input_file: str, output_file: str):
    """Apply udapi block functions to a full treebank document."""
    doc = Document(filename=input_file)

    # Processing full document
    spaceafter = SetSpaceAfterFromText()
    spaceafter.run(document=doc)

    fix_multisubj = FixMultiSubjects()
    fix_multisubj.run(document=doc)

    fix_leaf = FixLeaf(deprels="aux,cop,case,mark,cc,det")
    fix_leaf.run(document=doc)

    fix_chain = FixChain()
    fix_chain.run(document=doc)

    fix_right = FixRightheaded()
    fix_right.run(document=doc)

    fixpunct = FixPunct(check_paired_punct_upos=True)
    fixpunct.run(document=doc)

    normalize_order = Normalize()
    normalize_order.run(document=doc)

    # Write the modified document to an output file
    doc.store_conllu(output_file)


# %%


def report_errors(report_file: Path, output_file: str | Path = "-") -> pd.DataFrame:
    """Parse the error report from the UniversalDependencies/tools/validate.py script,
    and print a compressed report with the sum of each error type.

    Args:
        filepath: Path to the validation report file. Should be a Path for a txt-file.
        output_file: Path to write output report to. Default is -, which means it'll just print to the terminal window.
    """
    rows = report_file.read_text(encoding="utf-8").splitlines()

    error_info_regx = re.compile(
        r"^\["
        + r"(?:File )?(?P<file>[^ ]+)?\s*"
        + r"(?:Line )?(?P<line>\d+)?\s*"
        + r"(?:Sent )?(?P<sent>\d+)?\s*"
        + r"(?:Node )?(?P<node>\d+)?"
        + r"\]: \["
        + r"(?P<error_level>L[1234])"
        + " "
        + r"(?P<error_class>\w+)"
        + " "
        + r"(?P<error_name>[\w-]+)"
        + r"\] "
        + r"(?P<error_message>.*)"
        + r"$"
    )

    errors = []
    for row in rows:
        m = error_info_regx.fullmatch(row)
        if m is None:
            logging.debug("Row didn't match the error regex pattern: %s", row)
            continue
        errors.append(m.groupdict())

    df = pd.DataFrame(errors)
    type_counts = df.value_counts(subset=["error_level", "error_class", "error_name"])

    if str(output_file).startswith("-"):
        print("## Summary \n")
        print(type_counts)
    else:
        type_counts.to_csv(output_file)

    return df


def remove_comment_lines(input_file: str, output_file: str):
    """Remove all lines starting with `#` from a file."""
    with open(input_file, "r") as infile, open(output_file, "w") as outfile:
        outfile.writelines(line for line in infile if not line.startswith("#"))


# %%
