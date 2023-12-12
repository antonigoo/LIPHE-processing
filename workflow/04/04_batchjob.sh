#!/bin/bash
#SBATCH --job-name=04_clipping_trees
#SBATCH --account=project_2008498
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=15G
#SBATCH --partition=small

module purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

BASE_PATH="/scratch/project_2008498/antongoo/fgi/test_data/"
BASE_NAME="200406_100502_Sample"

input_las="${BASE_PATH}output/${BASE_NAME}_resampled.las"
output_dir="${BASE_PATH}output/single_trees/"

srun python 04_clipping_trees.py $input_las $output_dir
