#!/usr/bin/env bash


TODAY=$(date +%d-%m-%y)

DATA_DIR="data"
ORIGINAL_TREEBANK="$DATA_DIR/dev_fixed_UDfeats.conll"  # or test_fixed_UDfeats.conll or training_fixed_UDfeats.conll
CONVERTED_TREEBANK="$DATA_DIR/ud2-9_conversion_output_${TODAY}.conllu"

RULES_DIR="rules"
GRS_FILE="$RULES_DIR/mainstrategy.grs"
STRATEGY="main"


grew transform \
  -i  $ORIGINAL_TREEBANK \
  -o  $CONVERTED_TREEBANK \
  -grs  $GRS_FILE \
  -strat $STRATEGY \
  -safe_commands
