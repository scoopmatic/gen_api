# gen_api

After cloning this repository, run: `git submodule update --init --recursive`

Download generation model file: `wget -P models http://dl.turkunlp.org/textgen/hockey_gen_api_models/gen_model_v2.pt`

Requirements: `pip install sentencepiece`

Configuration of processing unit for generation: in `generate_v2.sh` set `GPU=-1` for CPU or `0` for first GPU

