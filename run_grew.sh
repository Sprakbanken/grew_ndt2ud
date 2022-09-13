#!/usr/bin/env bash


TODAY=$(date +%d-%m-%y)

#DATA_DIR="../trebankdatabase/data/SUD/SUD_Norwegian-Bokmaal/no_bokmaal-sud-train.conllu "
#ORIGINAL_TREEBANK="$DATA_DIR/no_bokmaal-sud-train.conllu "  # or test_fixed_UDfeats.conll or training_fixed_UDfeats.conll
#CONVERTED_TREEBANK="$DATA_DIR/sud2ud_conversion_output_${TODAY}.conllu"

ORIGINAL_TREEBANK="data/sentences/even_one_more_sentence.conll"
CONVERTED_TREEBANK="data/output_${TODAY}.conll"

GRS_FILE="rules/mainstrategy.grs"
STRATEGY="main"


grew transform \
  -i  $ORIGINAL_TREEBANK \
  -o  $CONVERTED_TREEBANK \
  -grs  $GRS_FILE \
  -strat main \
  -safe_commands
