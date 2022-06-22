#!/usr/bin/env bash


export today=$(date +%d-%m-%y)

RULES_DIR="rules"
STRAT_FILE=${1:-"mainstrategy.grs"}
STRAT_NAME=${2:-"main"}
DATA_DIR="data"
CORPUS_FILE=${3:-"dev_fixed_UDfeats.conll"}
OUTFILE=${4:-"ud2-9_conversion_output_${today}.conllu"}


grew transform -grs "${RULES_DIR}/${STRAT_FILE}" -strat $STRAT_NAME -i "${DATA_DIR}/${CORPUS_FILE}" -o "${DATA_DIR}/${OUTFILE}"
