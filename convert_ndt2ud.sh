
# Treebank file names
PARTITION=dev
#PARTITION=train
#PARTITION=test
#LANG=nn
LANG=nb

NDT_FILE=data/ndt_${LANG}_${PARTITION}_udmorph.conllu
#CONVERTED=data/grew_output_${LANG}_${PARTITION}.conllu
CONVERTED=data/grew_output_${PARTITION}.conllu
TEMPFILE=tmp.conllu
REPORTFILE=validation-report_ndt2ud_${LANG}_${PARTITION}.txt

# File names for testing
#NDT_FILE=data/sentences/testsents.conllu
#CONVERTED=OUTPUT.conllu
#TEMPFILE=deleteme.conllu


# START CONVERSION
echo "--- Convert $LANG $PARTITION treebank ---"

grew transform \
    -i  $NDT_FILE \
    -o  $CONVERTED \
    -grs  rules/NDT_to_UD.grs \
    -safe_commands

echo "--- Fix punctuation ---"
cat $CONVERTED | udapy -s ud.FixPunct > $TEMPFILE

grew transform \
    -i $TEMPFILE \
    -o $CONVERTED \
    -grs rules/NDT_to_UD.grs \
    -strat "postfix" \
    -safe_commands

# EVALUATION
echo "--- Validate treebank with UD validation script ---"
python ../tools/validate.py --max-err 0 --lang no $CONVERTED 2>&1 | tee $REPORTFILE

python extract_errorlines.py \
    -f $REPORTFILE \
    -e right-to-left-appos  # hent ut linjene for en spesifikk feilmeldingstype (-e errortype) fra valideringsrapporten


echo "--- Remove comment lines for MaltEval ---"
python parse_conllu.py -rc -f $CONVERTED -o $TEMPFILE
MALTGOLD=malt_input.conllu
python parse_conllu.py -rc -f $NDT_FILE -o $MALTGOLD

echo "--- Validate treebank with MaltEval ---"
UD_OFFICIAL=data/${LANG}-ud-${PARTITION}_uten_hash.conllu

for METRIC in UAS LAS; do
    java -jar dist-20141005/lib/MaltEval.jar \
        -s tmp.conllu \
        -g $UD_OFFICIAL \
        --GroupBy Deprel \
        --Metric $METRIC \
    > conversion_stats_${LANG}_${PARTITION}_${METRIC}.txt

    java -jar dist-20141005/lib/MaltEval.jar \
        -s tmp.conllu \
        -g $UD_OFFICIAL \
        --Metric $METRIC
done

# VISUALISATION
echo "--- Visualize converted treebank ---"
java -jar dist-20141005/lib/MaltEval.jar -g $MALTGOLD -s $TEMPFILE -v 1
