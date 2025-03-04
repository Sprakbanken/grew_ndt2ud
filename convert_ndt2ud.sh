#!/bin/bash

# Define variables
LANG="nb"
#LANG="nn"

#PARTITION="gold"
#PARTITION="test"
PARTITION="dev"
#PARTITION="train"

while getopts "p:l:v" opt; do
  case $opt in
    p) PARTITION=$OPTARG ;;
    l) LANG=$OPTARG ;;
    v) VISUALIZE=1 ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    :) echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
  esac
done


if [[ $LANG = "nb" ]]; then
NAME=bokmaal
elif [ $LANG = "nn" ]; then
NAME=nynorsk
else
echo "Invalid language argument: $LANG" >&2; exit 1
fi

if [ $PARTITION = "gold" ]; then
# Convert a sample of NDT and compare with the manually corrected gold standard for UD bokmål
NDT_FILE=data/gullkorpus/2019_gullkorpus_ndt.conllu
CONVERTED=data/gullkorpus/output.conllu
UD_OFFICIAL=data/gullkorpus/2023_gullkorpus_ud.conllu
LANG=nb
elif [ $PARTITION = "dev" ] || [ $PARTITION = "train" ] || [ $PARTITION = "test" ]; then
# Convert one of the splits and compare with the previously released UD version
NDT_FILE=data/ndt_aligned_with_ud/ndt_${LANG}_${PARTITION}.conllu
CONVERTED=data/converted/no_${NAME}-ud-${PARTITION}.conllu
#UD_OFFICIAL=data/${LANG}-ud-${PARTITION}_uten_hash.conllu
UD_OFFICIAL=data/UD_official/no_${NAME}-ud-${PARTITION}.conllu
else
echo "Invalid argument: $PARTITION" >&2; exit 1
fi

# Create temporary directory
TEMPDIR="tmp"
mkdir -p $TEMPDIR

#TEMPFILE=tmp.conllu
#TMP2=tmp2.conllu
REPORTFILE=validation-report_ndt2ud_${LANG}_${PARTITION}.txt

echo "--- CONVERT TREEBANK ---"
echo "Language: $LANG"
echo "Partition: $PARTITION"
echo "NDT file: $NDT_FILE"
echo "Output will be written to '$CONVERTED' and '$REPORTFILE'"


# START CONVERSION
echo "--- Convert morphology: feats and pos-tags ---"
TEMPFILE="${TEMPDIR}/01_convert_morph_output.conllu"
python utils/convert_morph.py -f $NDT_FILE -o $TEMPFILE

# Add MISC annotation 'SpaceAfter=No'
TEMPOUT="${TEMPDIR}/02_udapy_spaceafter.conllu"
#cat $TEMPFILE | udapy -s ud.SetSpaceAfterFromText  > $TEMPOUT
python utils/udapi_tools.py -i $TEMPFILE -o $TEMPOUT -p space
TEMPFILE=$TEMPOUT


echo "--- Convert dependency relations ---"
TEMPOUT=$TEMPDIR/03_grew_transform_deprels.conllu

grew transform \
    -i  $TEMPFILE \
    -o  $TEMPOUT \
    -grs  rules/NDT_to_UD.grs \
    -strat "main_$LANG" \
    -safe_commands

TEMPFILE=$TEMPOUT

echo "--- Fix punctuation ---"
TEMPOUT=$TEMPDIR/04_udapy_fixpunct.conllu
#cat $TEMPFILE | udapy -s ud.FixPunct  > $TEMPOUT
python utils/udapi_tools.py -i $TEMPFILE -o $TEMPOUT -p punct
TEMPFILE=$TEMPOUT

echo "--- Fix errors introduced by udapy ---"
TEMPOUT=$TEMPDIR/05_grew_transform_postprocess.conllu
grew transform \
    -i $TEMPFILE \
    -o $TEMPOUT \
    -grs rules/NDT_to_UD.grs \
    -strat "postprocess" \
    -safe_commands
TEMPFILE=$TEMPOUT

# Remove comment line with column names and replace invalid newpar lines
TEMPOUT=$TEMPDIR/06_replace_newpar.conllu
sed -e 's/\#  = \# newpar/\# newpar/g' $TEMPFILE > $TEMPOUT
TEMPFILE=$TEMPOUT
cp $TEMPFILE $CONVERTED

# EVALUATION
echo "--- Validate treebank with UD validation script ---"
python tools/validate.py --max-err 0 --lang no $CONVERTED 2>&1 | tee $REPORTFILE

python utils/extract_errorlines.py \
    -f $REPORTFILE #-e right-to-left-appos  # hent ut linjene for en spesifikk feilmeldingstype (-e errortype) fra valideringsrapporten


echo "--- Remove comment lines for MaltEval ---"
TEMPOUT=$TEMPDIR/07_remove_comments.conllu
python utils/parse_conllu.py -rc -f $TEMPFILE -o $TEMPOUT
TEMPFILE=$TEMPOUT

MALTGOLD=malt_ud_official.conllu
python utils/parse_conllu.py -rc -f $UD_OFFICIAL -o $MALTGOLD

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
if [ "$VISUALIZE" = 1 ]; then
    echo "--- Visualize converted treebank ---"
    java -jar dist-20141005/lib/MaltEval.jar -g $MALTGOLD -s $TEMPFILE -v 1
fi


echo "--- Conversion finished ---"
echo rm -rf $TEMPDIR
