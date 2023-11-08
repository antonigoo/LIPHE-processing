#!/bin/bash
#SBATCH --job-name=01_add_parameters_and_normalize
#SBATCH --account=project_2008498
#SBATCH --time=01:10:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=200G
#SBATCH --partition=small

module load geoconda

input_las=/scratch/project_2008498/antongoo/fgi/data/200406_100502.laz
output_las=/scratch/project_2008498/antongoo/fgi/data/output/200406_100502_normalized.las

srun python 01_add_parameters_and_normalize.py $input_las $output_las
