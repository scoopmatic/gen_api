# Pipeline for launching event selection model

TMP=/tmp/gen_api
SESSION=$(head /dev/urandom |md5sum| cut -b-4)

mkdir $TMP 2> /dev/null
mkdir $TMP/$SESSION

python convert_json.py example.json $TMP/$SESSION/events.json

cd ../game-report-generator
python create_training_data_orig.py $TMP/$SESSION/events.json /dev/null /dev/null $TMP/$SESSION/events_for_selection.jsonl $TMP/$SESSION/events_ext.json

cd ../event-selector
python gen_crf_feats.py $TMP/$SESSION/events_for_selection.jsonl $TMP/$SESSION/events_for_selection.jsonl $TMP/$SESSION/sel
crfsuite/frontend/crfsuite tag -m crf.model -s label_bias=1:0.85 $TMP/$SESSION/sel_val.tsv > $TMP/$SESSION/crf.pred

cd ../game-report-generator
python insert_selection.py $TMP/$SESSION/events.json $TMP/$SESSION/events_for_selection.jsonl $TMP/$SESSION/crf.pred $TMP/$SESSION/events_selected.json
# Predicted event selection marked in events_selected.json

# Save stripped event selection JSON data into output.json
echo "import json; d=json.load(open('events_selected.json')); json.dump({g: [e['selected'] for e in d[g]['events'] ] for g in d}, open('output.json','w'), indent=2)" | python3

#rm -rf $TMP/$SESSION
