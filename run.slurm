#!/bin/bash

#SBATCH --job-name=score-extraction

#SBATCH --partition=ex_scioi_a100nv,ex_scioi_gpu
#SBATCH --constraint=cuda13&tesla_a100|tesla_a10080G
#SBATCH --time=8:00:00

#SBATCH --output=slurm/%j.out
#SBATCH --error=slurm/%j.err

#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=32G
#SBATCH --gres=gpu:1

#SBATCH --mail-type=begin,end,fail
#SBATCH --mail-user=m.ploner@campus.tu-berlin.de

# sent a SIGINT signal 60 seconds before terminating the process due to timeout
#SBATCH --signal=SIGINT@60



echo "Running on $(hostname)"


module avail
echo "-----------------------------"

module load cuda/13.2
#module load python/3.9.19 


###########################################

echo "Setting environment variables"

# set up proxy (no internet on nodes)
#export https_proxy=http://frontend01:3128/
#export http_proxy=http://frontend01:3128/



# https://github.com/pytorch/pytorch/issues/111469#issuecomment-1869208750
#export LD_LIBRARY_PATH=$HOME/permutation_lm/.venv/lib/python3.9/site-packages/nvidia/nvjitlink/lib:$LD_LIBRARY_PATH

export TOKENIZERS_PARALLELISM=false
export HF_DATASETS_CACHE=$HOME/.cache/huggingface
export GIT_PYTHON_REFRESH="quiet"
export CUDA_LAUNCH_BLOCKING=1
export UV_TORCH_BACKEND=auto

###########################################



srun uv run process-extractions.py ${@:1}



experiments_exit_code=$?



exit $experiments_exit_code
