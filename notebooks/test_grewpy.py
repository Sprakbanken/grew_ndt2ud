from pathlib import Path
from grewpy import Graph, Corpus, GRSDraft, Rule, Request, Commands, GRS, set_config
import json

set_config("ud")

corpus = Corpus("data/sentences/testsents.conllu")
graph = corpus[8]

print ("  Build a GRS from a file (data/sentences/testsents.conllu)")
grs = GRS("rules/appositions.grs")
print (grs)


new_graph = grs.run(graph, strat="APP_main")[0]

conll_str = Graph(new_graph).to_conll()

outfile = Path("grewpy_output.conllu")

outfile.write_text(conll_str)

