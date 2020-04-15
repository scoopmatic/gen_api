this=$1
fname=$2

GPU=-1 #0=Use first GPU; -1=Use CPU

source $this/../venv-stt/bin/activate

cd event2text-attnctrl
bash generate_aug_live.sh ../tmp_files $fname.input $fname.output $GPU
