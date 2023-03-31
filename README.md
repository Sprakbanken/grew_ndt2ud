# Konvertering av NDT til UD med GREW

## Innhold

- [Arbeidsflyt](#arbeidsflyt)
- [Eksempeldrevet arbeidsflyt](#eksempeldrevet-arbeidsflyt)
- [Hjelpeskript](#hjelpeskript)
- [Referanser](#referanser)
- [Filstruktur](#filstruktur)

## Arbeidsflyt

1. Kjøre reglene vi allerede har på et av datasettene:

    Du kan endre miljøvariabelen `PARTITION` fra `train` til `dev` når vi vil sjekke hvor langt vi har kommet.

    Den første linjen i den konverterte conll-filen `$CONVERTED` lister opp kolonnenavnene, og gir feilmelding med MaltEval: `# global.columns = ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC`. Den siste kommandoen i kodeblokken under fjerner denne linjen.

    ```shell
    PARTITION=train

    NDT_FILE=data/ndt_nb_${PARTITION}_udmorph.conllu
    CONVERTED=data/grew_output_${PARTITION}.conllu

    grew transform \
      -i  $NDT_FILE \
      -o  $CONVERTED \
      -grs  rules/mainstrategy.grs \
      -strat main \
      -safe_commands
    ```

2. Valider utdata med UD's valideringsskript:

   Hvis du har udapi installert, kan du også fikse tegnsettingen før du validerer:

   ``` shell
   cat $CONVERTED | udapy -s ud.FixPunct > tmp.conllu  && mv tmp.conllu $CONVERTED
   ```

   Kjør valideringsskriptet:

   ``` shell
   python ../tools/validate.py --max-err 0 --lang no $CONVERTED 2>&1 | tee validation-report_ndt2ud.txt
   ```

   Hent ut en oppsummering av valideringsrapporten:

   ``` shell
   python extract_errorlines.py -f validation-report_ndt2ud.txt
   ```

3. Sammenligne resultatet med tidligere versjon av UD

   Fjern kommentarlinjer fra utdata før du kjører MaltEval, som forventer [CONLL-X-formatet](https://aclanthology.org/W06-2920.pdf):

    ```shell
    python parse_conllu.py -rc -f $CONVERTED -o tmp.conllu
    ```

   a. Statistikk over relasjoner

      I hvor stor grad matcher relasjonene i konversjonen ift. UD på
      - at relasjonen `R(x,y)` finnes i den andre trebanken, med samme etikett, og mellom de samme nodene? --> Sett `METRIC=LAS` (Labelled Accuracy Score) i kommandoen under.
      - at det finnes en relasjon `R(x,y)` mellom nodene `x` og `y` (uavhengig av etikett)? --> Sett `METRIC=UAS`

      ```shell
      METRIC=UAS
      UD_OFFICIAL=data/no_bokmaal-ud-${PARTITION}_uten_hash.conllu

      java -jar dist-20141005/lib/MaltEval.jar -s tmp.conllu -g $UD_OFFICIAL --GroupBy Deprel --Metric $METRIC > conversion_stats_${METRIC}.txt
      ```

      Bytt ut `METRIC`-variabelen og kjør kommandoen på nytt for å få begge statistikkene.

   b. Overblikk i MaltEval

      Se visuell sammenligning av setningsgrafene, og søk etter relasjonene som har flest feil (dårligst score fra pkt a.)

      ```shell
      java -jar dist-20141005/lib/MaltEval.jar -s tmp.conllu -g $UD_OFFICIAL -v 1
      ```

   c. Valider conll-fil med egendefinerte pos-tags og deprel:

      ```shell
      java -jar MaltEval.jar -s parser.conll -g gold.conll --postag gold.postag --deprel gold.deprel
      ```


4. Skrive regler som håndterer de høyfrekvente feilene

     - Legg inn regel i en grs-fil i [rules/](./rules/) (Se [grew dokumentasjon](https://grew.fr/doc/rule/))
     - Legg inn referanse til regelsett eller regel i [mainstrategy.grs](./rules/mainstrategy.grs)


## Eksempeldrevet arbeidsflyt

1. Finn eksempelsetninger på et syntaktisk fenomen med MaltEval.

    Se på strukturelle forskjeller mellom UD og NDT for 200 utvalgte setninger med MaltEval.

      ```shell
      java -jar dist-20141005/lib/MaltEval.jar -s data/gullkorpus/2019_gullkorpus_ud_før_annotasjon_uten_hash.conllu data/gullkorpus/2019_gullkorpus_ndt_uten_hash.conllu -g data/gullkorpus/2019_gullkorpus_ud_uten_hash.conllu -v 1
      ```

2. Kjør grew på eksempelsetninger med en teststrategi

    Samle alle eksempelsetningene fra `data/sentences` i én fil, eller oppgi hvilken setningsfil du vil konvertere.

    ```shell
    INPUT=data/sentences/all.conll
    cat data/sentences/* > $INPUT
    ```

    Test reglene som brukes i `rules/teststrategy.grs`.

    ```shell
    grew transform \
      -i  $INPUT \
      -o  data/output.conll \
      -grs  rules/teststrategy.grs \
      -strat main \
      -safe_commands
    ```

    I `rules/teststrategy.grs`: filtrer regler/pakker/strategier fra `Seq()`-lista i `strat test`-strategien med kommentarsymbolet `%`

## Hjelpeskript

Filen [`2023_gullkorpus_ud.conllu`](./data/gullkorpus/2023_gullkorpus_ud.conllu) inneholder 200 setninger fra den norske UD-trebanken for bokmål. Setningene er blitt rettet manuelt og kan brukes til å teste konverteringen av NDT.

1. I notebooken `process_NDT.ipynb` er det kode for å hente ut UD-partisjonene fra gullkorpuset.

2. `convert_morph.py` konverterer conll-feltene "feats" og "upos" fra NDT sine merkelapper til UD sine.

  ```shell
  python convert_morph.py -f 'data/gullkorpus/2019_gullkorpus_ndt.conllu' -o 'data/gullkorpus/2019_gullkorpus_ndt_udmorph.conllu'
  ```

3. Modulen "parse_conllu.py" har et flagg `-rc` som fjerner kommentarlinjene fra Conll-filen.

  ```shell
  python parse_conllu.py -rc -f $FILENAME
  ```

4. Fiks tegnsetting, terminalnoder, og skift hoder fra høyre til venstre  i conlldata med [udapi](https://udapi.github.io/):

```
cat $CONVERTED | udapy -s ud.FixPunct ud.FixRightheaded ud.FixLeaf > out.conllu
```

## Referanser

- [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
- [Graph Matching and Graph Rewriting: GREW tools for corpus exploration, maintenance and conversion](https://aclanthology.org/2021.eacl-demos.21) (Guillaume, EACL 2021)
- [Dependency Parsing with Graph Rewriting](https://aclanthology.org/W15-2204) (Guillaume & Perrier, 2015)

## Filstruktur

```shell
$ tree --gitignore -L 2

.
├── conversion_stats_LAS.txt
├── conversion_stats_UAS.txt
├── data
│   ├── grew_output_train.conllu
│   ├── gullkorpus
│   ├── ndt_nb_dev_udfeatspos.conllu
│   ├── ndt_nb-NO.conllu
│   ├── ndt_nb_test_udfeatspos.conllu
│   ├── ndt_nb_train_udfeatspos.conllu
│   ├── ndt_nn_dev_udfeatspos.conllu
│   ├── ndt_nn_test_udfeatspos.conllu
│   ├── ndt_nn_train_udfeatspos.conllu
│   ├── no_bokmaal-ud-dev_uten_hash.conllu
│   ├── no_bokmaal-ud-test_uten_hash.conllu
│   ├── no_bokmaal-ud-train_uten_hash.conllu
│   ├── sentences
│   └── UD_v2-11
├── dist-20141005
├── fetch_sents_by_ID.sh
├── notebooks
│   ├── grew_book_code.ipynb
│   ├── test_grew.ipynb
│   └── test_grew_rule_application.ipynb
├── partition_data.py
├── README.md
├── rules
│   ├── grew_example_rules.grs
│   ├── mainstrategy.grs
│   ├── NDT_to_UD.grs
│   ├── relabel_NDT_to_UD_deprel.grs
│   ├── reverse_heads.grs
│   ├── shift_root.grs
│   ├── SUD_to_UD.grs
│   ├── testrules.grs
│   └── teststrategy.grs
└── utils
    └── MaltEval-dist.zip

8 directories, 29 files
```
