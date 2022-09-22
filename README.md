# Konvertering av NDT til UD med GREW

## Kjør grew fra kommandolinjen


```
TODAY=$(date +%d-%m-%y_%H%M%S)

grew transform \
  -i  "data/training_fixed_UDfeats.conll" \
  -o  "data/output/${TODAY}.conll" \
  -grs  rules/mainstrategy.grs \
  -strat main \
  -safe_commands
```

Test ut enkeltregler på enkeltsetninger med `rules/teststrategy.grs`: 

```
TODAY=$(date +%d-%m-%y_%H%M%S)

grew transform \
  -i  "data/sentences/yet_another_sentence.conll" \
  -o  "data/output/${TODAY}.conll" \
  -grs  rules/teststrategy.grs \
  -strat main \
  -safe_commands
```

I `rules/teststrategy.grs`: filtrer regler/pakker/strategier fra `Seq()`-lista i `strat test`-strategien med kommentarsymbolet `%`


## Repo-struktur

```
% tree --gitignore
.
├── data
│   ├── 2019_gullkorpus_ndt.conllu
│   ├── 2019_gullkorpus_ndt_dev_uten_hash.conllu
│   ├── 2019_gullkorpus_ndt_train_uten_hash.conllu
│   ├── 2019_gullkorpus_ndt_uten_hash.conllu
│   ├── 2019_gullkorpus_ud.conllu
│   ├── 2019_gullkorpus_ud_dev_uten_hash.conllu
│   ├── 2019_gullkorpus_ud_før_annotasjon.conllu
│   ├── 2019_gullkorpus_ud_før_annotasjon_dev_uten_hash.conllu
│   ├── 2019_gullkorpus_ud_før_annotasjon_train_uten_hash.conllu
│   ├── 2019_gullkorpus_ud_før_annotasjon_uten_hash.conllu
│   ├── 2019_gullkorpus_ud_train_uten_hash.conllu
│   ├── 2019_gullkorpus_ud_uten_hash.conllu
│   ├── dev_fixed_UDfeats.conll
│   ├── gullkorpus_all_ids.txt
│   ├── gullkorpus_dev_ids.txt
│   ├── gullkorpus_train_ids.txt
│   ├── ndt_nb-NO.conllu
│   ├── output
│   ├── sample1_training_fixed_UDfeats.conll
│   ├── sample2_training_fixed_UDfeats.conll
│   ├── sentences
│   │   ├── another_sentence.conll
│   │   ├── even_one_more_sentence.conll
│   │   ├── just_another_sentence.conll
│   │   ├── modal_aux.conllu
│   │   ├── one_sentence.conll
│   │   ├── skulle_ha_vaert_hovedsetning.conllu
│   │   └── yet_another_sentence.conll
│   ├── test_fixed_UDfeats.conll
│   └── training_fixed_UDfeats.conll
├── dist-20141005
├── fetch_sents_by_ID.sh
├── notebooks
│   ├── grew_book_code.ipynb
│   ├── test_grew.ipynb
│   └── test_grew_rule_application.ipynb
├── partition_data.py
├── README.md
├── rules
│   ├── grew_example_rules.grs
│   ├── mainstrategy.grs
│   ├── NDT_to_UD.grs
│   ├── relabel_NDT_to_UD_deprel.grs
│   ├── reverse_heads.grs
│   ├── shift_sentence_root.grs
│   ├── SUD_to_UD.grs
│   ├── testrules.grs
│   └── teststrategy.grs
└── utils
    └── MaltEval-dist.zip

7 directories, 44 files
```

## MaltEval diff

```
java -jar dist-20141005/lib/MaltEval.jar -s data/2019_gullkorpus_ud_før_annotasjon_uten_hash.conllu data/2019_gullkorpus_ndt_uten_hash.conllu -g data/2019_gullkorpus_ud_uten_hash.conllu -v 1
```

## Generer MaltEval-kompatible dev- og train-splitter av gullkorpuset

```
./fetch_sents_by_ID.sh
```

## Referanser
* [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
* [Graph Matching and Graph Rewriting: GREW tools for corpus exploration, maintenance and conversion](https://aclanthology.org/2021.eacl-demos.21) (Guillaume, EACL 2021)

