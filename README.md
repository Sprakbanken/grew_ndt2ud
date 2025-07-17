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
  unzip MaltEval-dist.zip
  ```

4. Clone the official [UD tools](https://github.com/UniversalDependencies/tools/) repo for validating UD conllu files.

  ``` shell
  git clone git@github.com:UniversalDependencies/tools.git
  ```

## Convert the treebank

The conversion pipeline can be run with the CLI script `ndt2ud`:

``` shell
❯ python -m ndt2ud -h
connected to port: XXX
usage: ndt2ud [-h] -l LANGUAGE -i INPUT [-o OUTPUT] [-r REPORT] [-val VALIDATION_SCRIPT] [-g GREW_RULES]

Convert NDT treebank to UD format

options:
  -h, --help            show this help message and exit
  -l, --language LANGUAGE
                        Language (must be nb or nn)
  -i, --input INPUT     Input NDT file or folder
  -o, --output OUTPUT   Output UD file (default: UD_output.conllu)
  -r, --report REPORT   Validation report file (default: validation-report.txt)
  -val, --validation_script VALIDATION_SCRIPT
                        path to the UD tools validation script
  -g, --grew_rules GREW_RULES
                        File path to the grew GRS file with rules to convert the treebank with.
```

## Evaluate the treebanks dependency relations

Compare the conversion result with a previous version of UD with [MaltEval](https://www.maltparser.org/malteval.html). See the [User Guide pdf](dist-20141005/doc/MaltEvalUserGuide.pdf) for more info.

Score the dependency relation accuracy with (`--Metric LAS`) or without (`--Metric UAS`) dependency labels.

- **UAS / Unlabelled Accuracy Score**: whether a directed relation R(x,y) exists between the same nodes x, y in the other treebank
- **LAS / Labelled Accuracy Score**: whether the labelled, directed relation R(x,y) exists between nodes x,y

```shell
# Remove commented lines
grep -v '^#' {PATH_TO_CONVERTED_TREEBANK} > {PATH_TO_TREEBANK_WITHOUT_COMMENTS}

# Run the evaluation
java -jar dist-20141005/lib/MaltEval.jar \
  -s {PATH_TO_TREEBANK_WITHOUT_COMMENTS} \
  -g {PATH_TO_GOLD_STANDARD} \
  --GroupBy Deprel \
  --Metric LAS \
> conversion_stats.txt
```

## Visualize sentence graphs

```shell
# Remove commented lines
grep -v '^#' {PATH_TO_CONVERTED_TREEBANK} > {PATH_TO_TREEBANK_WITHOUT_COMMENTS}

# Run viewer tool
java -jar dist-20141005/lib/MaltEval.jar \
  -v 1 \
  -s {PATH_TO_TREEBANK_WITHOUT_COMMENTS} \
  -g {PATH_TO_GOLD_STANDARD}
```

## Grew rules

The [`rules`](./rules)-folder contains `grs`-files with [`grew` rules](https://grew.fr/doc/rule/) and [strategies](https://grew.fr/doc/grs/) which are applied in a certain order.
The `main_nb` (bokmål) and `main_nn` (nynorsk) strategies in [`rules/NDT_to_UD.grs`](rules/NDT_to_UD.grs) define the respective pipelines that modify the sentence graphs in the treebank.

See the notebook [`notebooks/rule_workflow.ipynb`](notebooks/rule_workflow.ipynb) (in Norwegian, with python) for a step-by-step approach to writing rules.

See also the Grew documentation on [requests](https://grew.fr/doc/request/) and [commands](https://grew.fr/doc/commands/) for more information about the syntax.

## Resources

- [`data/2023_gullkorpus_ud.conllu`](./data/gullkorpus/2023_gullkorpus_ud.conllu) contains 200 manually corrected sententes from the Norwegian bokmål UD treebank. This gold standard is used to evaluate the conversion.
- [UD annotation guidelines](https://universaldependencies.org/guidelines.html)
- [NDT annotation guidelines](https://www.nb.no/sbfil/dok/20140314_guidelines_ndt_english.pdf)
- [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
- [Graph Matching and Graph Rewriting: GREW tools for corpus exploration, maintenance and conversion](https://aclanthology.org/2021.eacl-demos.21) (Guillaume, EACL 2021)
- [Dependency Parsing with Graph Rewriting](https://aclanthology.org/W15-2204) (Guillaume & Perrier, 2015)
