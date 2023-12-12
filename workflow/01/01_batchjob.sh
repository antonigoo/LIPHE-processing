#!/bin/bash
#SBATCH --job-name=01_add_parameters_and_normalize
#SBATCH --account=project_2008498
#SBATCH --time=01:10:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=200GB
#SBATCH --partition=small
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

module purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

BASE_PATH="/scratch/project_2008498/antongoo/fgi/test_data/"
BASE_NAME="200406_100502_Sample"

input_las="${BASE_PATH}${BASE_NAME}.laz"
output_las="${BASE_PATH}output/${BASE_NAME}_normalized.las"

srun python 01_add_parameters_and_normalize.py $input_las $output_las
