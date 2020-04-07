this=$1
fname=$2

GPU=0 #0=Use first GPU; -1=Use CPU

source $this/../venv-stt/bin/activate

#python $this/../OpenNMT-py/translate.py -model $this/../OpenNMT-py/hockey/saved_models/generation_model_nodalida.pt -src tmp_files/$fname.input -output tmp_files/$fname.output -replace_unk
cd event2text-attnctrl
bash generate_aug_live.sh ../tmp_files $fname.input $fname.output $GPU
