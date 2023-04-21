
# Treebank file names
#PARTITION=train
#NDT_FILE=data/ndt_nb_${PARTITION}_udmorph.conllu
#CONVERTED=data/grew_output_${PARTITION}.conllu
#TEMPFILE=tmp.conllu

# File names for testing
NDT_FILE=data/sentences/testsents.conllu
CONVERTED=OUTPUT.conllu
TEMPFILE=deleteme.conllu


# START CONVERSION
echo "--- Convert treebank ---"

grew transform \
    -i  $NDT_FILE \
    -o  $CONVERTED \
    -grs  rules/NDT_to_UD.grs \
    -safe_commands

#echo "--- Fix punctuation ---"
#cat $CONVERTED | udapy -s ud.FixPunct > $TEMPFILE

#grew transform \
#    -i $TEMPFILE \
#    -o $CONVERTED \
#    -grs rules/post_udapy_fixes.grs \
#    -safe_commands

# EVALUATION
#echo "--- Validate treebank ---"
#python ../tools/validate.py --max-err 0 --lang no $CONVERTED 2>&1 | tee validation-report_ndt2ud.txt

#python extract_errorlines.py \
#    -f validation-report_ndt2ud.txt #\
    # -e right-to-left-appos  # hent ut linjene for en spesifikk feilmeldingstype (-e errortype) fra valideringsrapporten


# VISUALISATION
echo "--- Remove comment lines ---"
MALTGOLD=malt_input.conllu
python parse_conllu.py -rc -f $CONVERTED -o $TEMPFILE
python parse_conllu.py -rc -f $NDT_FILE -o $MALTGOLD

echo "--- Visualize converted treebank ---"
java -jar dist-20141005/lib/MaltEval.jar -g $MALTGOLD -s $TEMPFILE -v 1

