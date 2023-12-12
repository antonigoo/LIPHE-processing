#!/bin/bash
#SBATCH --job-name=06_fine_segmentation
#SBATCH --account=project_2008498
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=5G
#SBATCH --partition=small

module purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

BASE_PATH="/scratch/project_2008498/antongoo/fgi/test_data/"
BASE_NAME="200406_100502_Sample"

input_las_dir="${BASE_PATH}output/single_trees_normalized_to_ground/"
output_las_dir=/"${BASE_PATH}output/fine_segmnentation/"
output_noise_dir="${BASE_PATH}output/fine_segmnentation_noise/"

srun python 06_fine_segmentation.py $input_las_dir $output_las_dir $output_noise_dir
