import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import grewpy
import pandas as pd
from grewpy import Request
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


@dataclass
class Node:
    name: str
    node_id: str | None = None
    parent: str | None = None
    children: list | None = None
    feats: dict = field(default_factory=dict)

    def __post_init__(self):
        for k, v in self.feats.items():
            setattr(self, k, v)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        # Keep feats dict in sync with attribute changes, except for special/private attributes
        if key not in {
            "name",
            "node_id",
            "parent",
            "children",
            "feats",
        } and not key.startswith("_"):
            self.feats[key] = value

    def __repr__(self):
        return f"{self.name} [ {', '.join(feat + '=' + str(value) for feat, value in self.feats.items())} ]"


@dataclass
class Edge:
    source: str
    target: str
    label: str = ""
    name: str = "e"

    def __repr__(self):
        return f"{self.name}: {self.source} -[{self.label}]-> {self.target}"


def strip_feats(token_features: dict):
    features = token_features.copy()
    del features["__RAW_MISC__"]
    del features["textform"]
    del features["wordform"]

    return features


def view_search_results(request: Request, treebank: grewpy.Corpus):
    """Print the matching results in the treebank"""

    print(f"Antall treff: {treebank.count(request)}")
    print(request, "\n")

    print("Setninger som matcher mønsteret: ")
    for occ in treebank.search(request):  # type: ignore
        sent_id = occ["sent_id"]
        print(f"{sent_id=}")

        graph = treebank.get(sent_id)
        text = graph.to_sentence()
        print(f"{text=}")  # type: ignore

        for node_name, node_id in occ["matching"]["nodes"].items():
            features = strip_feats(graph.features[node_id])
            token = Node(name=node_name, node_id=node_id, feats=features)
            print(f"Node {node_id}: {token}")

        for edge_name, edge in occ["matching"]["edges"].items():
            e = Edge(name=edge_name, **edge)
            print(f"Edge {edge_name} ({e.source} -> {e.target}): {e.label}")

        print()
