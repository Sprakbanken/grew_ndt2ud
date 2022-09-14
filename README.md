# Konvertering av NDT til UD med GREW

## Kjør grew fra kommandolinjen


```
TODAY=$(date +%d-%m-%y_%H%M%S)

grew transform \
  -i  "data/sentences/one_sentence.conll" \
  -o  "data/output/${TODAY}.conll" \
  -grs  mainstrategy.grs \
  -strat main \
  -safe_commands
```

## Repo-struktur

```
# grew-testing
.
├── data
│   ├── 2019_gullkorpus_ud.conllu
│   ├── 2019_gullkorpus_ud_før_annotasjon.conllu
│   ├── dev_fixed_UDfeats.conll
│   ├── GULL_dev.csv
│   ├── GULL_dev_ids.txt
│   ├── GULL_train.csv
│   ├── GULL_train_ids.txt
│   ├── output
│   ├── sample1_training_fixed_UDfeats.conll
│   ├── sample2_training_fixed_UDfeats.conll
│   ├── sentences
│   │   ├── another_sentence.conll
│   │   ├── another_sentence_rev.conll
│   │   ├── even_one_more_sentence.conll
│   │   ├── just_another_sentence.conll
│   │   ├── one_sentence.conll
│   │   ├── one_sentence_headrev.conll
│   │   └── yet_another_sentence.conll
│   ├── test_fixed_UDfeats.conll
│   └── training_fixed_UDfeats.conll
├── notebooks
│   ├── grew_book_code.ipynb
│   ├── test_grew.ipynb
│   └── test_grew_rule_application.ipynb
├── README.md
└── rules
    ├── func_dep_rel.grs
    ├── mainstrategy.grs
    ├── NDT_to_UD.grs
    ├── reverse_heads.grs
    ├── SUD_to_UD.grs
    ├── testrule.grs
    ├── test_rules.grs
    └── teststrategy.grs

5 directories, 30 files
```
## MaltEval diff

```
java -jar MaltEval_dist-20141005/lib/MaltEval.jar -s 2019_gullkorpus_ud_før_annotasjon_uten-hash.conllu -g 2019_gullkorpus_ud_uten-hash.conllu -v 1
```

## Referanser
* [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
* [Graph Matching and Graph Rewriting: GREW tools for corpus exploration, maintenance and conversion](https://aclanthology.org/2021.eacl-demos.21) (Guillaume, EACL 2021)

