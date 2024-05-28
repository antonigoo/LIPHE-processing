#!/bin/bash
#SBATCH --job-name=nextflow_slurm
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2G
#SBATCH --partition=small

module load nextflow
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

nextflow run workflow.nf -c slurm.config --base_path "/scratch/project_2008498/antongoo/fgi/nextflow_many_files" 
