#!/bin/bash
#SBATCH --job-name=posture
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

mkdir -p logs
cd "$(dirname "$0")"
source ~/.bashrc
conda activate ml 2>/dev/null || source venv/bin/activate

python "$@"
