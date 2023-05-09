
# Treebank file names

#PARTITION=dev
#PARTITION=train
#PARTITION=test
PARTITION=gull

LANG=nb
#NAME=bokmaal
#LANG=nn
#NAME=nynorsk

#NDT_FILE=data/ndt_${LANG}_${PARTITION}.conllu
#CONVERTED=data/converted/no_${NAME}-ud-${PARTITION}.conllu
TEMPFILE=tmp.conllu
REPORTFILE=validation-report_ndt2ud_${LANG}_${PARTITION}.txt
#UD_OFFICIAL=data/${LANG}-ud-${PARTITION}_uten_hash.conllu

# File names for testing against the gold standard
NDT_FILE=data/gullkorpus/2019_gullkorpus_ndt.conllu
CONVERTED=gull_konvertert.conllu
UD_OFFICIAL=data/gullkorpus/2023_gullkorpus_ud.conllu
TMP2=deleteme.conllu

# START CONVERSION
echo "--- Convert $LANG $PARTITION treebank ---"

echo "--- Morphology: feats and pos-tags ---"
python convert_morph.py -f $NDT_FILE -o $TEMPFILE

echo "--- Add MISC annotation 'SpaceAfter=No' ---"
cat $TEMPFILE | udapy -s ud.SetSpaceAfterFromText  > $TMP2 && mv $TMP2 $TEMPFILE


echo "--- Dependency relations ---"
grew transform \
    -i  $TEMPFILE \
    -o  $CONVERTED \
    -grs  rules/NDT_to_UD.grs \
    -strat "main_$LANG" \
    -safe_commands

echo "--- Fix punctuation ---"
# add ud.SetSpaceAfterFromText after ud.FixPunct for the nb dev set!
cat $CONVERTED | udapy -s ud.FixPunct  > $TEMPFILE

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
    #-e right-to-left-appos  # hent ut linjene for en spesifikk feilmeldingstype (-e errortype) fra valideringsrapporten


echo "--- Remove comment lines for MaltEval ---"
python parse_conllu.py -rc -f $CONVERTED -o $TEMPFILE
MALTGOLD=malt_input.conllu
#python parse_conllu.py -rc -f $NDT_FILE -o $MALTGOLD
python parse_conllu.py -rc -f $UD_OFFICIAL -o $MALTGOLD

echo "--- Validate treebank with MaltEval ---"

for METRIC in UAS LAS; do
    java -jar dist-20141005/lib/MaltEval.jar \
        -s $TEMPFILE \
        -g $MALTGOLD  \
        --GroupBy Deprel \
        --Metric $METRIC \
    > conversion_stats_${LANG}_${PARTITION}_${METRIC}.txt

    java -jar dist-20141005/lib/MaltEval.jar \
        -s $TEMPFILE \
        -g $MALTGOLD  \
        --Metric $METRIC
done

# VISUALISATION
echo "--- Visualize converted treebank ---"
java -jar dist-20141005/lib/MaltEval.jar -g $MALTGOLD -s $TEMPFILE -v 1
