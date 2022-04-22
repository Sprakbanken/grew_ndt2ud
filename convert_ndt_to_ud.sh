#!/usr/bin/env bash

ORIGINAL_TREEBANK=no_bokmaal-ud-train.conllu
CONVERTED_TREEBANK=grew_output.conllu
GRS_FILE=teststrategy.grs
STRATEGY=s_1

grew transform \
  -grs  $GRS_FILE \
  -i  $ORIGINAL_TREEBANK \
  -o  $CONVERTED_TREEBANK \
  -strat $STRATEGY \
  -safe_commands
