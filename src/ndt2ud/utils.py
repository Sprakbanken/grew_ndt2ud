import logging
import re
import urllib.request
from pathlib import Path

import pandas as pd
from udapi import Document
from udapi.block.ud.fixchain import FixChain
from udapi.block.ud.fixleaf import FixLeaf
from udapi.block.ud.fixmultisubjects import FixMultiSubjects
from udapi.block.ud.fixpunct import FixPunct
from udapi.block.ud.fixrightheaded import FixRightheaded
from udapi.block.ud.setspaceafterfromtext import SetSpaceAfterFromText
from udapi.block.util.normalize import Normalize


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


def report_errors(report_file: Path, error_type: str | None = None) -> None:
    """Parse the error report from the UniversalDependencies/tools/validate.py script,
    and print a compressed report with the sum of each error type.

    Args:
        filepath: Path to the validation report file. Should be a Path for a txt-file.
        error_type: specific error type to filter on.
            The error messages for the given type are printed to a csv file.
    """
    rows = report_file.read_text(encoding="utf-8").splitlines()

    error_info_regx = re.compile(
        r"^\[Line (\d+)(?: Sent )?(\d+)?(?: Node )?(\d+)?\]\: \[(L.*)\] (.*)(\[[0-9]*, [0-9]*\])?(.*)?$",
        flags=re.DOTALL,
    )
    errors = []
    for row in rows:
        m = error_info_regx.fullmatch(row)
        if m is None:
            logging.debug("Couldn't match this with the regex pattern: %s", row)
            continue
        errors.append(m.groups())

    df = pd.DataFrame(
        errors,
        columns=[
            "line",
            "sent",
            "node",
            "errortype",
            "message",
            "relevant_nodes",
            "message2",
        ],
    )
    if error_type is not None:
        df[df.errortype.str.contains(error_type)].to_csv(
            f"error_{error_type}.csv", index=False
        )

    type_counts = df.errortype.value_counts()

    print("Validation report summary:")
    print(type_counts.sort_index())
