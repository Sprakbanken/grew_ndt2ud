PARTITION=train

NDT_FILE=data/ndt_nb_${PARTITION}_udmorph.conllu
CONVERTED=data/grew_output_${PARTITION}.conllu
TEMPFILE=tmp.conllu

echo "Convert treebank"

grew transform \
    -i  $NDT_FILE \
    -o  $CONVERTED \
    -grs  rules/mainstrategy.grs \
    -strat main \
    -safe_commands

echo "Fix punctuation"
cat $CONVERTED | udapy -s ud.FixPunct > $TEMPFILE

grew transform \
    -i $TEMPFILE \
    -o $CONVERTED \
    -grs rules/post_udapy_fixes.grs \
    -safe_commands

echo "Validate treebank"
python ../tools/validate.py --max-err 0 --lang no $CONVERTED 2>&1 | tee validation-report_ndt2ud.txt

# endre verdien til -e (errortype) for å hente ut linjene til en spesifikk feiltype fra valideringsrapporten
python extract_errorlines.py -f validation-report_ndt2ud.txt -e rel-pos-advmod

echo "Remove comment lines"
python parse_conllu.py -rc -f $CONVERTED -o $TEMPFILE

echo "Visualize converted treebank"
java -jar dist-20141005/lib/MaltEval.jar -s $TEMPFILE -v 1


