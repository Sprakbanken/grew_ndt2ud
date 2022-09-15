#! /bin/env bash

# Trekk ut setnings-IDene fra gullkorpuset
cat data/2019_gullkorpus_ud.conllu | grep -E '# sent_id = [0-9]+' | sed -E 's/.*# sent_id = ([0-9]+)+.*/\1/g' > data/GULL_all_IDS.txt

# Overskriv innholdet i fila for utdata
echo "" > data/2019_gullkorpus_ndt.conllu 

# Trekk ut setningene som matcher gullkorpus-IDene fra NDT (i conllu-format)
for sent_id in $(cat data/GULL_all_IDS.txt )
do
    echo ${sent_id}
    sed -rn "/# sent_id = ${sent_id}/,/# internal_id/p" data/ndt_nb-NO.conllu |
    sed 's/# .*//' >> data/2019_gullkorpus_ndt_uten-hash.conllu 
done
