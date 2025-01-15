# Konvertering av NDT til UD med GREW

Repoet inneholder skript og regelfiler for å konvertere syntaktiske og morfologiske annotasjoner fra Norsk dependenstrebank ([NDT](https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-10/)) til Universal Dependencies ([UD](https://universaldependencies.org/)).

Regelfilene er skrevet for [Grew](https://grew.fr/), som må [installeres](https://grew.fr/usage/install/) før konverteringsskriptet kan kjøres.

## Oppsett

- [Python](https://www.python.org/downloads/)
- [Grew installation](https://grew.fr/usage/install/)
- [udapi](https://udapi.github.io/):

  ``` shell
  pip3 install --user --upgrade udapi
  ```

- [MaltEval](https://www.maltparser.org/malteval.html):

  ``` shell
  unzip utils/MaltEval-dist.zip
  ```

- [UD tools](https://github.com/UniversalDependencies/tools/):

  ``` shell
  cd ..
  git clone git@github.com:UniversalDependencies/tools.git
  ```

## Konverter trebanken

``` shell
./convert_ndt2ud.sh -v
```

Skriptet tar tre valgfrie argumenter:

| flagg | gyldige verdier | beskrivelse |
| ---|---|---|
| `-l` | `nb`, `nn` | Språkkode på 2 bokstaver. Default er `nb`. |
| `-p` | `dev`, `test`, `train`, `gold` | Datasett-splitt (partisjon). Default er `gold`, dvs. gullstandardutvalget på 200 manuelt korrigerte setninger. |
| `-v` |  | Visualiser forskjellene mellom siste offisielle versjon av UD og den nye konverteringen med MaltEval. |

## Arbeidsprosess

Regelfilene ble utviklet med følgende fremgangsmåte.

1. Kjør reglene på et av datasettene med grew:

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

2. Fiks tegnsetting:

   Vi bruker [udapi](https://udapi.github.io/) + egne post-prosesseringsregler for å fikse setningsintern tegnsetting.

   ``` shell
   cat $CONVERTED | udapy -s ud.FixPunct > tmp.conllu

   grew transform \
    -i tmp.conllu \
    -o $CONVERTED \
    -grs rules/NDT_to_UD.grs \
    -strat "postfix" \
    -safe_commands

   # Remove comment line with column names
   sed -i 1d $CONVERTED
   ```

3. Valider utdata med [UD's valideringsskript](https://github.com/UniversalDependencies/tools/blob/master/validate.py):

   ``` shell
   python ../tools/validate.py --max-err 0 --lang no $CONVERTED 2>&1 | tee validation-report_ndt2ud.txt
   python utils/extract_errorlines.py -f validation-report_ndt2ud.txt
   ```

4. Sammenlign resultatet med tidligere versjon av UD

   Fjern kommentarlinjer fra utdata før du kjører [MaltEval](https://www.maltparser.org/malteval.html), som forventer [CONLL-X-formatet](https://aclanthology.org/W06-2920.pdf):

    ```shell
    python utils/parse_conllu.py -rc -f $CONVERTED -o tmp.conllu
    ```

   a. Statistikk over relasjoner

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

      Bytt ut `METRIC`-variabelen og kjør kommandoen på nytt for å få begge statistikkene.

   b. Visualiser og sammenlign setningsgrafene i MaltEval

      ```shell
      java -jar dist-20141005/lib/MaltEval.jar -s tmp.conllu -g $UD_OFFICIAL -v 1
      ```

### Grew-regler

[rules-mappen](./rules/) inneholder `grs`-filer med [regler](https://grew.fr/doc/rule/) og [strategier](https://grew.fr/doc/grs/) som datasettet kjøres gjennom. Rekkefølgen reglene appliseres i er definert i strategiene `main_nn` og `main_nb` i [NDT_to_UD.grs](rules/NDT_to_UD.grs)

Se også Grew-dokumentasjonen om [kommandoer](https://grew.fr/doc/commands/).

### Match setninger med grew-mønstre

Vi brukte også `grew grep` for å søke etter setninger og utvikle [mønstre for grew requests](https://grew.fr/doc/request/).

``` shell
grew grep -request rules/testpattern.req -i $NDT_FILE > pattern_matches.json
```

### Datautvalg

For bestemte fenomener har vi samlet noen eksempelsetninger i `data/sentences`-mappen, og testet enkeltregler og ulike regelstrategier på disse.

Setningene som listes i `pattern_matches.json` kan skrives til en egen `conllu`-fil. Se eksempelkode for å gjøre dette i [`process_NDT.ipynb`](process_NDT.ipynb).

### Teststrategi

```shell
grew transform \
  -i  $INPUT \
  -o  data/output.conll \
  -grs  rules/teststrategy.grs \
  -strat test \
  -safe_commands
```

### Hjelpeskript

- [`2023_gullkorpus_ud.conllu`](./data/gullkorpus/2023_gullkorpus_ud.conllu) inneholder 200 setninger fra den norske UD-trebanken for bokmål. Setningene er blitt rettet manuelt og kan brukes til å teste konverteringen av NDT.

- Notebooken [`process_NDT.ipynb`](process_NDT.ipynb) har kode for å hente ut spesifikke setninger med setningsID-er, konvertere morfologiske trekk, og utforske dataene.

- `utils/convert_morph.py` konverterer conllu-feltene "feats" og "upos" fra NDT sine merkelapper til UD sine.

```shell
python utils/convert_morph.py -f 'data/gullkorpus/2019_gullkorpus_ndt.conllu' -o 'data/gullkorpus/2019_gullkorpus_ndt_udmorph.conllu'
```

- Modulen `utils/parse_conllu.py` har et flagg `-rc` som fjerner kommentarlinjene fra Conll-filen.

``` shell
python utils/parse_conllu.py -rc -f data/gullkorpus/2019_gullkorpus_ndt.conllu -o data/gullkorpus/2019_gullkorpus_ndt_uten_hash.conllu
```

- Fiks tegnsetting, terminalnoder, og skift hoder fra høyre til venstre  i conlldata med [udapi](https://udapi.github.io/):

``` shell
cat $CONVERTED | udapy -s ud.FixPunct ud.FixRightheaded ud.FixLeaf > out.conllu
```

## Referanser

- [UD retningslinjer](https://universaldependencies.org/guidelines.html)
- [NDT retningslinjer](https://www.nb.no/sbfil/dok/20140314_guidelines_ndt_english.pdf) (engelsk)
- [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
- [Graph Matching and Graph Rewriting: GREW tools for corpus exploration, maintenance and conversion](https://aclanthology.org/2021.eacl-demos.21) (Guillaume, EACL 2021)
- [Dependency Parsing with Graph Rewriting](https://aclanthology.org/W15-2204) (Guillaume & Perrier, 2015)
