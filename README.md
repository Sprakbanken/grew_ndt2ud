# Convert NDT to UD with Grew

This repo contains scripts and rule files to convert syntactic and morphological annotations from the Norwegian dependency treebank [NDT](https://www.nb.no/sprakbanken/en/resource-catalogue/oai-nb-no-sbr-10/) to Universal Dependencies [UD](https://universaldependencies.org/).

The rules are written with [Grew](https://grew.fr/) which needs to be [installed](https://grew.fr/usage/install/) prior to running the conversion script.

## Setup

1. Install the command line tool Grew: [Grew installation](https://grew.fr/usage/install/)

2. Create a virtual environment and install the project dependencies. You can use pdm or uv to manage the project installation:

  ```shell
  # Option: pdm
  pdm install

  # Option: uv
  uv sync
  ```

3. Extract the java tool [MaltEval](https://www.maltparser.org/malteval.html) from the zipped file in `./utils/`

  ``` shell
  unzip utils/MaltEval-dist.zip
  ```

4. Clone the official [UD tools](https://github.com/UniversalDependencies/tools/) repo for validating UD conllu files.

  ``` shell
  git clone git@github.com:UniversalDependencies/tools.git
  ```

## Convert the treebank

The whole conversion pipeline can be run with a single python script:

``` shell
❯ pdm run python -m grew_ndt2ud -h
connected to port: 33783
usage: __main__.py [-h] -i INPUT -l LANGUAGE [-o OUTPUT] [-r REPORT]

Convert NDT treebank to UD format

options:
  -h, --help            show this help message and exit
  -i, --input INPUT     Input NDT file
  -l, --language LANGUAGE
                        Language (must be nb or nn)
  -o, --output OUTPUT   Output UD file (default: UD_output.conllu)
  -r, --report REPORT   Validation report file (default: validation-report.txt)
```

## Visualize and evaluate the treebank with MaltEval

Compare the result with a previous version of UD

1. Remove comment lines from the file before running it through [MaltEval](https://www.maltparser.org/malteval.html).

```shell
python utils/parse_conllu.py -rc -f $CONVERTED -o tmp.conllu
```

2. Evaluate relation statistics

  **UAS / Unlabelled Accuracy Score**: whether a directed relation R(x,y) exists between the same nodes x, y in the other treebank
  **LAS / Labelled Accuracy Score**: whether the labelled, directed relation R(x,y) exists between nodes x,y

Score the relation accuracy with (`--Metric LAS`) or without (`--Metric UAS`) dependency labels.

```shell
java -jar dist-20141005/lib/MaltEval.jar \
  -s {PATH_TO_CONVERTED_TREEBANK} \
  -g {PATH_TO_GOLD_STANDARD} \
  --GroupBy Deprel \
  --Metric LAS #or UAS \
> conversion_stats.txt
```

3. Visualize and compare sentence graphs in MaltEval

```shell
java -jar dist-20141005/lib/MaltEval.jar -s {PATH_TO_CONVERTED_TREEBANK} -g {PATH_TO_GOLD_STANDARD} -v 1
```

## Grew rules

The [rules-folder](./rules/) contains `grs`-files with [rules](https://grew.fr/doc/rule/) and [strategies](https://grew.fr/doc/grs/) which are applied in a certain order, as defined in the `main_nb` and `main_nn` strategies in [NDT_to_UD.grs](rules/NDT_to_UD.grs).

See also the Grew documentation on [commands](https://grew.fr/doc/commands/) for more information.

### Match sentences with Grew pattens

We also used `grew grep` to match sentences and develop [request patterns](https://grew.fr/doc/request/) for the rules, to ensure we targeted the correct structures.

``` shell
grew grep -request rules/testpattern.req -i $NDT_FILE -html -dep_dir data/search_results > data/search_results/pattern_matches.json
```


### Utilities

- [`2023_gullkorpus_ud.conllu`](./data/gullkorpus/2023_gullkorpus_ud.conllu) contains 200 manually corrected sententes from the Norwegian bokmål UD treebank. This gold standard is used to evaluate the conversion.

- The jupyter notebook [`process_NDT.ipynb`](process_NDT.ipynb) was used for data exploration and to develop intermediate processing steps.

- [`utils/convert_morph.py`](utils/convert_morph.py) converts the conllu columns `FEATS` and `UPOS` from NDT to UD labels.

```shell
python utils/convert_morph.py -f 'data/gullkorpus/2019_gullkorpus_ndt.conllu' -o 'data/gullkorpus/2019_gullkorpus_ndt_udmorph.conllu'
```

- [`utils/parse_conllu.py`](utils/convert_morph.py) can be run with the flag `-rc` to remove comment lines from a conllu file.

``` shell
python utils/parse_conllu.py -rc -f data/gullkorpus/2019_gullkorpus_ndt.conllu -o data/gullkorpus/2019_gullkorpus_ndt_uten_hash.conllu
```

- [udapi](https://udapi.github.io/) is used to add `SpaceAfter=No` to the `MISC` field, fix projectivity and punctuation issues, etc:

``` shell
cat $CONVERTED | udapy -s ud.SetSpaceAfterFromText ud.FixPunct ud.FixRightheaded ud.FixLeaf > out.conllu
```

## References

- [UD annotation guidelines](https://universaldependencies.org/guidelines.html)
- [NDT annotation guidelines](https://www.nb.no/sbfil/dok/20140314_guidelines_ndt_english.pdf)
- [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
- [Graph Matching and Graph Rewriting: GREW tools for corpus exploration, maintenance and conversion](https://aclanthology.org/2021.eacl-demos.21) (Guillaume, EACL 2021)
- [Dependency Parsing with Graph Rewriting](https://aclanthology.org/W15-2204) (Guillaume & Perrier, 2015)
