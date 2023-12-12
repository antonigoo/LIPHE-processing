#!/bin/bash
#SBATCH --job-name=03_spatial_resample
#SBATCH --account=project_2008498
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=160G
#SBATCH --partition=small

module purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

BASE_PATH="/scratch/project_2008498/antongoo/fgi/test_data/"
BASE_NAME="200406_100502_Sample"

input_las="${BASE_PATH}output/${BASE_NAME}_georef.las"
output_las="${BASE_PATH}output/${BASE_NAME}_resampled.las"

srun python 03_spatial_resample.py $input_las $output_las
