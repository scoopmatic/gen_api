this=$1
fname=$2

source $this/../venv-stt/bin/activate

python $this/../OpenNMT-py/translate.py -model $this/../OpenNMT-py/hockey/saved_models/model_step_22500.pt -src tmp_files/$fname.input -output tmp_files/$fname.output
