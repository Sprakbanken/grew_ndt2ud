#! /bin/env bash



# filnavn
GULLFIL="data/2019_gullkorpus_ud.conllu"
UD_FIL="data/2019_gullkorpus_ud_før_annotasjon.conllu"
NDT_FIL="data/2019_gullkorpus_ndt.conllu"
DEV_IDS="data/gullkorpus_dev_ids.txt"
TRAIN_IDS="data/gullkorpus_train_ids.txt"


function trekk_ut_gull_fra_ndt () {
    # Trekk ut setnings-IDene fra gullkorpuset
    grep -E '# sent_id = [0-9]+' data/2019_gullkorpus_ud.conllu | sed -E 's/.*# sent_id = ([0-9]+)+.*/\1/g' > data/gullkorpus_all_ids.txt

    # Trekk ut setningene som matcher gullkorpus-IDene i NDT-conllu-filen    
    for sent_id in $(cat data/gullkorpus_all_ids.txt ); do
        sed -rn "/# sent_id = ${sent_id}/,/# internal_id/p" "data/ndt_nb-NO.conllu" | sed '/# internal.*/d' >> $NDT_FIL
    done
}

# trekk_ut_gull_fra_ndt

python ./partition_data.py $GULLFIL $UD_FIL $NDT_FIL -f $DEV_IDS $TRAIN_IDS
