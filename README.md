# Convert NDT to UD with Grew

This repo contains scripts and rule files to convert syntactic and morphological annotations from the Norwegian dependency treebank [NDT](https://www.nb.no/sprakbanken/en/resource-catalogue/oai-nb-no-sbr-10/) to Universal Dependencies [UD](https://universaldependencies.org/).

The rules are written with [Grew](https://grew.fr/) which needs to be [installed](https://grew.fr/usage/install/) prior to running the conversion script.

## Setup

1. Install the command line tool Grew: [Grew installation](https://grew.fr/usage/install/)

2. Create a virtual environment and install the project dependencies. You can use pdm, uv or the python module venv:

  ```shell
  # Option: python venv
  python -m venv .venv 
  source .venv/bin/activate 
  pip install -r requirements.txt 

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

### Alternative 1: Shell script

The whole conversion pipeline can be run with a single shell script:

``` shell
./convert_ndt2ud.sh -v
```

The script can take three optional arguments:

| flag | valid arguments | description |
| ---|---|---|
| `-l` | `nb`, `nn` | 2 letter language code for bokmål and nynorsk. Default is `nb`. |
| `-p` | `dev`, `test`, `train`, `gold` | Dataset split (partition). Default is `dev`, ie. the development set with approx. 2400 sentences. |
| `-v` |  | Visualize the differences between the last official UD version and the new converted conllu file with MaltEval. |

### Alternative 2: Step by step

The conversion can also be run step-by-step in the terminal. 


#### Development process

The rules were developed with the following step-by-step approach.

1. Run Grew with the main strategy file:

    ```shell
    LANG=nb
    PARTITION=dev #train
    NDT_FILE=data/ndt_${LANG}_${PARTITION}_udmorph.conllu
    CONVERTED=data/grew_output_${PARTITION}.conllu

    grew transform \
      -i  $NDT_FILE \
      -o  $CONVERTED \
      -grs  rules/NDT_to_UD.grs \
      -strat "main_$LANG" \
      -safe_commands
    ```

2. Fix punctuation:

   We use udapi  [udapi](https://udapi.github.io/) + our own post processing rules to fix head attachment and direction of relations to the sentence internal punctuations.

   ``` shell
   cat $CONVERTED | udapy -s ud.FixPunct > tmp.conllu

   grew transform \
    -i tmp.conllu \
    -o $CONVERTED \
    -grs rules/NDT_to_UD.grs \
    -strat "postprocess" \
    -safe_commands

   # Remove comment line with column names
   tail -n +2  $CONVERTED > tmp.conllu && mv tmp.conllu $CONVERTED
   ```

3. Validate the output with [UD's validation script](https://github.com/UniversalDependencies/tools/blob/master/validate.py):

   ``` shell
   python tools/validate.py --max-err 0 --lang no $CONVERTED 2>&1 | tee validation-report_ndt2ud.txt
   python utils/extract_errorlines.py -f validation-report_ndt2ud.txt
   ```

4. Compare the result with a previous version of UD

   Remove comment lines from the file before running it through [MaltEval](https://www.maltparser.org/malteval.html).

    ```shell
    python utils/parse_conllu.py -rc -f $CONVERTED -o tmp.conllu
    ```

   a. Relation statistics

      Swap the commented `METRIC` line to score the relation accuracy with or without dependency labels.

      ```shell
      # UAS / Unlabelled Accuracy Score: whether a directed relation R(x,y) exists between the same nodes x, y in the other treebank
      # LAS / Labelled Accuracy Score: whether the labelled, directed relation R(x,y) exists between nodes x,y
      METRIC=LAS
      #METRIC=UAS
      UD_OFFICIAL=data/${LANG}-ud-${PARTITION}_uten_hash.conllu

      java -jar dist-20141005/lib/MaltEval.jar \
        -s tmp.conllu \
        -g $UD_OFFICIAL \
        --GroupBy Deprel \
        --Metric $METRIC \
      > conversion_stats_${LANG}_${PARTITION}_${METRIC}.txt
      ```

   b. Visualize and compare sentence graphs in MaltEval

      ```shell
      java -jar dist-20141005/lib/MaltEval.jar -s tmp.conllu -g $UD_OFFICIAL -v 1
      ```

## Grew rules

The [rules-folder](./rules/) contains `grs`-files with [rules](https://grew.fr/doc/rule/) and [strategies](https://grew.fr/doc/grs/) which are applied in a certain order, as defined in the `main_nb` and `main_nn` strategies in [NDT_to_UD.grs](rules/NDT_to_UD.grs).

See also the Grew documentation on [commands](https://grew.fr/doc/commands/) for more information.

### Match sentences with Grew pattens

We also used `grew grep` to match sentences and develop [request patterns](https://grew.fr/doc/request/) for the rules, to ensure we targeted the correct structures.

``` shell
grew grep -request rules/testpattern.req -i $NDT_FILE -html -dep_dir data/search_results > data/search_results/pattern_matches.json
```

### Data selection

We gathered a few example sentences in the [`data/sentences`](data/sentences/) folder to try out the effects of different patterns, rules and strategies. Example code to extract the matched sentences in `pattern_matches.json` from NDT to a separate conllu file can be found in the jupyter notebook [`process_NDT.ipynb`](process_NDT.ipynb).

### Test strategy

```shell
grew transform \
  -i  data/sentences/testsents.conllu \
  -o  data/output.conll \
  -grs  rules/teststrategy.grs \
  -strat test \
  -safe_commands
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
