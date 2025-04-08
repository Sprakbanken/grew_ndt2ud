#!/bin/bash

# Handle user input arguments
while getopts "i:l:o:r:" opt; do
 case $opt in
    i) INPUT_FILE=$OPTARG ;;
    l) L=$OPTARG ;;          # Must be nb or nn
    o) OUTPUT_FILE=$OPTARG ;;
    r) REPORTFILE=$OPTARG ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    :) echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
  esac
done

: "${INPUT_FILE:?Need to set input file}"
: "${L:?Need to set language with -l nb or -l nn}"
: "${OUTPUT_FILE:=UD_output.conllu}"  # Set default output file name if not provided
: "${REPORTFILE:=validation-report.txt}"  # Set default report file name if not provided

# Create temporary directory
TEMPDIR="tmp"
mkdir -p $TEMPDIR

echo "--- CONVERT NDT TREEBANK to UD ---"
echo ""
echo "--- Input parameters ---"
echo "  Language: $L"
echo "  Input NDT file: $INPUT_FILE"
echo "  Output UD file: $OUTPUT_FILE"
echo "  Validation report: $REPORTFILE"
echo ""

# START CONVERSION

echo "--- Convert morphology: feats and pos-tags ---"
TEMPFILE="${TEMPDIR}/01_convert_morph_output.conllu"
python utils/convert_morph.py -f $INPUT_FILE -o $TEMPFILE

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
    -strat "main_$L" \
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
cp $TEMPFILE $OUTPUT_FILE

# EVALUATION
echo "--- Validate treebank with UD validation script ---"
python tools/validate.py --max-err 0 --lang no $OUTPUT_FILE 2>&1 | tee $REPORTFILE

python utils/extract_errorlines.py \
    -f $REPORTFILE #-e right-to-left-appos  # hent ut linjene for en spesifikk feilmeldingstype (-e errortype) fra valideringsrapporten

echo "--- Conversion finished ---"
#echo rm -rf $TEMPDIR
