#!/bin/bash
#
#SBATCH --mail-type=END,FAIL
#SBATCH --job-name=moco_ash
#SBATCH --partition=trc
#SBATCH --time=96:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --output=/home/users/asmart/projects/justmoco/logs/%x.%j.out
#SBATCH --open-mode=append

module use /home/groups/trc/modules
module load antspy/0.2.2

python3 /home/users/asmart/projects/justmoco/motion_correction.py /oak/stanford/groups/trc/data/Ashley2/imports/20210716_2/fly1_20s_anat-010
