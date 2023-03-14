#! /bin/env bash



# filnavn
GULLFIL="data/gullkorpus/2023_gullkorpus_ud.conllu"
UD_UTVALG="data/gullkorpus/2019_gullkorpus_ud_før_annotasjon.conllu"
NDT_UTVALG="data/gullkorpus/2019_gullkorpus_ndt.conllu"

DEV_IDS="data/gullkorpus/gullkorpus_dev_ids.txt"
TRAIN_IDS="data/gullkorpus/gullkorpus_train_ids.txt"
GULL_IDS="data/gullkorpus/gullkorpus_all_ids.txt"

NDT_NB_ALL="data/ndt_nb-NO.conllu"



function trekk_ut_gull_fra_ndt () {
    # Trekk ut setnings-IDene fra gullkorpuset
    grep -E '# sent_id = [0-9]+' $GULLFIL | sed -E 's/.*# sent_id = ([0-9]+)+.*/\1/g' > $GULL_IDS

    # Trekk ut setningene som matcher gullkorpus-IDene i NDT-conllu-filen
    for sent_id in $(cat $GULL_IDS ); do
        sed -rn "/# sent_id = ${sent_id}/,/# internal_id/p" $NDT_NB_ALL | sed '/# internal.*/d' >> $NDT_UTVALG
    done
}

trekk_ut_gull_fra_ndt
