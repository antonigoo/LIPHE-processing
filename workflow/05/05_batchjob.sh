#!/bin/bash
#SBATCH --job-name=05_normalize_to_ground
#SBATCH --account=project_2008498
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=15G
#SBATCH --partition=small

module load geoconda

input_las_dir=/scratch/project_2008498/antongoo/fgi/data/output/single_trees/
output_dir=/scratch/project_2008498/antongoo/fgi/data/output/single_trees_normalized_to_ground/

srun python 05_normalize_to_ground.py $input_las_dir $output_dir
