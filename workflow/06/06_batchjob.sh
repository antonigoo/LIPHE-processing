#!/bin/bash
#SBATCH --job-name=06_fine_segmentation
#SBATCH --account=project_2008498
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=5G
#SBATCH --partition=small

module load geoconda
pip install opencv-python

input_las_dir=/scratch/project_2008498/antongoo/fgi/data/output/single_trees_normalized_to_ground/
output_las_dir=/scratch/project_2008498/antongoo/fgi/data/output/fine_segmnentation/
output_noise_dir=/scratch/project_2008498/antongoo/fgi/data/output/fine_segmnentation_noise/

srun python 06_fine_segmentation.py $input_las_dir $output_las_dir $output_noise_dir
