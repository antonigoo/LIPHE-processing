#!/bin/bash
#SBATCH --job-name=05_normalize_to_ground
#SBATCH --account=project_2008498
#SBATCH --time=00:05:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=15G
#SBATCH --partition=small

module purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

BASE_PATH="/scratch/project_2008498/antongoo/fgi/test_data/"
BASE_NAME="200406_100502_Sample"

input_las_dir="${BASE_PATH}output/single_trees/"
output_dir="${BASE_PATH}output/single_trees_normalized_to_ground/"

srun python 05_normalize_to_ground.py $input_las_dir $output_dir
