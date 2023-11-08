#!/bin/bash
#SBATCH --job-name=02_georeference
#SBATCH --account=project_2008498
#SBATCH --time=00:40:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=200G
#SBATCH --partition=small

module load geoconda

input_las=/scratch/project_2008498/antongoo/fgi/data/output/200406_100502_normalized.las
output_las=/scratch/project_2008498/antongoo/fgi/data/output/200406_100502_georef.las

srun python 02_georeference.py $input_las $output_las
