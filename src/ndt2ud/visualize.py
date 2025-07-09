import subprocess
from pathlib import Path
from typing import Generator

import grewpy
from spacy import displacy
from spacy_conll import init_parser
from spacy_conll.parser import ConllParser


def visualize_graph_displacy(
    graph: grewpy.graph.Graph,
    nlp: ConllParser | None = None,
    output_name: str | None = None,
) -> str:
    conllstr = graph.to_conll()

    if "nlp" not in globals():
        if nlp is None:
            nlp = ConllParser(init_parser("nb_core_news_md", "spacy"))

    doc = nlp.parse_conll_text_as_spacy(conllstr)  # type:ignore
    visual_graph = displacy.render(doc, style="dep", jupyter=False)
    if output_name is not None:
        Path(f"{output_name}.svg").write_text(visual_graph)
    return visual_graph


def visualize_treebank_displacy(
    input_file: str, nlp: ConllParser | None = None
) -> Generator:
    if nlp is None:
        nlp = ConllParser(init_parser("nb_core_news_lg", "spacy"))

    doc = nlp.parse_conll_file_as_spacy(input_file)

    # Multiple CoNLL entries (separated by two newlines) will be included as different sentences in the resulting Doc
    for sent in doc.sents:
        yield displacy.render(sent, style="dep", jupyter=False)


def visualize_graph_dot(graph: grewpy.graph.Graph, output_name: str) -> str | None:
    """Save as DOT file and convert to SVG"""
    if hasattr(graph, "to_dot"):
        dot_content = graph.to_dot()
        dot_file = f"{output_name}.dot"
        with open(dot_file, "w") as f:
            f.write(dot_content)  # type: ignore
        # print(f"✓ Saved DOT file: {dot_file}")

        # Convert DOT to SVG using graphviz

        svg_file = f"{output_name}.svg"
        result = subprocess.run(
            ["dot", "-Tsvg", dot_file, "-o", svg_file], capture_output=True, text=True
        )
        if result.returncode == 0:
            # print(f"✓ Converted to SVG: {svg_file}")
            return svg_file
        else:
            print(f"✗ DOT to SVG conversion failed: {result.stderr}")


def text_representation_graph(graph: grewpy.graph.Graph, output_name: str):
    """Create simple text representation of a sentence dependency graph"""
    print("\n📝 Text representation:")
    tokens = []

    for node_id in sorted(graph.order, key=int):
        node = graph[node_id]
        # Handle different node formats
        if isinstance(node, dict):
            form = node.get("form", f"TOKEN_{node_id}")
            tokens.append(f"{node_id}:{form}")
        elif hasattr(node, "__len__") and len(node) > 0:
            try:
                if isinstance(node[0], dict) and "form" in node[0]:
                    form = node[0]["form"]
                    tokens.append(f"{node_id}:{form}")
            except:
                tokens.append(f"{node_id}:?")

    print("Tokens:", " ".join(tokens))
    return "text_representation"
