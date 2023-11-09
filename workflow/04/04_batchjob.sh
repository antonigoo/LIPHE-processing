#!/bin/bash
#SBATCH --job-name=04_clipping_trees
#SBATCH --account=project_2008498
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=15G
#SBATCH --partition=small

module load geoconda
pip install openpyxl

input_las=/scratch/project_2008498/antongoo/fgi/data/output/200406_100502_resampled.las
output_dir=/scratch/project_2008498/antongoo/fgi/data/output/single_trees/

srun python 04_clipping_trees.py $input_las $output_dir
