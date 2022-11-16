# Konvertering av NDT til UD med GREW

## Arbeidsflyt

1. Kjøre reglene vi allerede har på hele treningssettet
    ```
    TODAY=$(date +%d-%m-%y_%H%M%S)

    grew transform \
      -i  data/training_fixed_UDfeats.conll \
      -o  data/output/out_${TODAY}.conll \
      -grs  rules/mainstrategy.grs \
      -strat main \
      -safe_commands
    ```
2. Sammenligne resultatet med tidligere versjon av UD 

   a. Overblikk i MaltEval

    ```
    UD_UTEN_HASH=<FYLL INN>  # ILD

    java -jar dist-20141005/lib/MaltEval.jar -s data/training_fixed_UDfeats.conll -g $UD_UTEN_HASH -v 1
    ```


   b. Score relasjoner ut fra likhet mellom vår konvertering og tidligere versjon av UD:
      - Hvilke ordklasser (felt 4) /evt. feats (felt 6) som oftest har feil hode (felt 7)
      - Hvilke NDT-relasjoner ender oftest med feil hode (og merkelapp)?
      - Hvilke UD-relasjonspar (vår vs. eldre) har feil merkelapp (felt 8)?
<--- [AK]: fyll inn kommando for malteval evaluering + dokumentasjon --->  

3. Skrive regler som håndterer de høyfrekvente feilene
     - Legg inn regel i en grs-fil i [rules/](./rules/)
     - Legg inn referanse til regelsett eller regel i [mainstrategy.grs](./rules/mainstrategy.grs)
     - Dokumentasjon på regelsyntaks på [grew.fr](https://grew.fr/doc/rule/)



## Eksempeldrevet arbeidsflyt
1.  Finn eksempelsetninger på et syntaktisk fenomen med MaltEval.

    Se på strukturelle forskjeller mellom UD og NDT for 200 utvalgte setninger med MaltEval. 

      ```
      java -jar dist-20141005/lib/MaltEval.jar -s data/2019_gullkorpus_ud_før_annotasjon_uten_hash.conllu data/2019_gullkorpus_ndt_uten_hash.conllu -g data/2019_gullkorpus_ud_uten_hash.conllu -v 1
      ```

2.  Kjør grew på eksempelsetninger med en teststrategi 

    Samle alle eksempelsetningene fra `data/sentences` i én fil, eller oppgi hvilken setningsfil du vil konvertere. 

    ```
    INPUT=data/sentences/all.conll
    cat data/sentences/* > $INPUT
    ```

    Test ut reglene som brukes i `rules/teststrategy.grs`.

    ```
    grew transform \
      -i  $INPUT \
      -o  data/output/out.conll \
      -grs  rules/teststrategy.grs \
      -strat main \
      -safe_commands
    ```

    I `rules/teststrategy.grs`: filtrer regler/pakker/strategier fra `Seq()`-lista i `strat test`-strategien med kommentarsymbolet `%`

## Repo-struktur

```
$ tree --gitignore
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
│   │   ├── clause_anticipating_presentational.conll
│   │   ├── clefting.conll
│   │   ├── copula_relative_passive.conll
│   │   ├── even_one_more_sentence.conll
│   │   ├── FSUBJ_SPRED_PSUBJ_subclause.conll
│   │   ├── just_another_sentence.conll
│   │   ├── modal_aux.conllu
│   │   ├── one_sentence.conll
│   │   ├── passive_sents.conllu
│   │   ├── presentational_PSUBJ.conll
│   │   ├── skulle_ha_vaert_hovedsetning.conllu
│   │   └── yet_another_sentence.conll
│   ├── test_fixed_UDfeats.conll
│   ├── training_fixed_UDfeats.conll
│   └── ud_vaere_aux_pass.conll
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
│   ├── shift_root.grs
│   ├── SUD_to_UD.grs
│   ├── testrules.grs
│   └── teststrategy.grs
└── utils
    └── MaltEval-dist.zip

7 directories, 51 files
```

## Splitt opp UD-gullkorpuset (200 rettede setninger)

Setningene i gullkorpuset er hentet fra to partisjoner, dev og train, av den norske UD-trebanken. 
Dette skriptet bruker filene `data/gullkorpus_*_ids.txt` for å dele opp gullkorpuset med den samme partisjoneringen.

```
./fetch_sents_by_ID.sh
```

## Referanser
* [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
* [Graph Matching and Graph Rewriting: GREW tools for corpus exploration, maintenance and conversion](https://aclanthology.org/2021.eacl-demos.21) (Guillaume, EACL 2021)
* [Dependency Parsing with Graph Rewriting](https://aclanthology.org/W15-2204) (Guillaume & Perrier, 2015)
