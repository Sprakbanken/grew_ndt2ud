# Konvertering av NDT til UD med GREW

## Kjør grew med shell-skript 

I skriptet kan du endre regel-filen (`*.grs`) og datasettet du bruker. 

```
./run_grew.sh

```

## Repo-struktur

``` 
|____README.md
|____notebooks
| |____*.ipynb
|____data
| |____sentences
| |____GULL_train.csv
| |____sample1_training_fixed_UDfeats.conll
| |____sample2_training_fixed_UDfeats.conll
| |____GULL_dev_ids.txt
| |____GULL_train_ids.txt
| |____GULL_dev.csv
|____run_grew.sh
|____rules
| |____allin1.grs
| |____NDT_to_UD.grs
| |____teststrategy.grs
| |____mainstrategy.grs
| |____func_dep_rel.grs
| |____test_rules.grs
| |____testrule.grs
| |____rev_heads.grs
| |____SUD_to_UD.grs

```

## Referanser
* [Starting a new treebank? Go SUD!](https://aclanthology.org/2021.depling-1.4) (Gerdes et al., DepLing 2021)
* 


