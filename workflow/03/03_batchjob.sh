#!/bin/bash
#SBATCH --job-name=03_spatial_resample
#SBATCH --account=project_2008498
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=160G
#SBATCH --partition=small

module load geoconda

input_las=/scratch/project_2008498/antongoo/fgi/data/output/200406_100502_georef.las
output_las=/scratch/project_2008498/antongoo/fgi/data/output/200406_100502_resampled.las

srun python 03_spatial_resample.py $input_las $output_las
