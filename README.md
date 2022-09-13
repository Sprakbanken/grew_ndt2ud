# Konvertering av NDT til UD med GREW

## Kjør grew med shell-skript 

I skriptet kan du endre regel-filen (`*.grs`) og datasettet du bruker. 

```
./run_grew.sh

```

## Repo-struktur

```
grew-testing
├── data
│   ├── 2019_gullkorpus_ud.conllu
│   ├── 2019_gullkorpus_ud_før_annotasjon.conllu
│   ├── dev_fixed_UDfeats.conll
│   ├── GULL_dev.csv
│   ├── GULL_dev_ids.txt
│   ├── GULL_train.csv
│   ├── GULL_train_ids.txt
│   ├── sample1_training_fixed_UDfeats.conll
│   ├── sample2_training_fixed_UDfeats.conll
│   ├── test_fixed_UDfeats.conll
│   ├── training_fixed_UDfeats.conll
│   └── sentences
│       ├── another_sentence.conll
│       ├── another_sentence_rev.conll
│       ├── even_one_more_sentence.conll
│       ├── just_another_sentence.conll
│       ├── one_sentence.conll
│       ├── one_sentence_headrev.conll
│       └── yet_another_sentence.conll
├── notebooks
│   ├── grew_book_code.ipynb
│   ├── Lesenotater.ipynb
│   ├── test_grew.ipynb
│   └── test_grew_rule_application.ipynb
├── README.md
├── rules
│   ├── func_dep_rel.grs
│   ├── mainstrategy.grs
│   ├── NDT_to_UD.grs
│   ├── reverse_heads.grs
│   ├── SUD_to_UD.grs
│   ├── testrule.grs
│   ├── test_rules.grs
│   └── teststrategy.grs
└── run_grew.sh

4 directories, 33 files
```

## Referanser
* [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
* [Graph Matching and Graph Rewriting: GREW tools for corpus exploration, maintenance and conversion](https://aclanthology.org/2021.eacl-demos.21) (Guillaume, EACL 2021)



