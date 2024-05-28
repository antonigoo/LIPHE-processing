#!/bin/bash
#SBATCH --job-name=nextflow_local
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=3
#SBATCH --mem-per-cpu=20G
#SBATCH --partition=small

module purge
module load nextflow
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

nextflow run workflow.nf --base_path "/scratch/project_2008498/antongoo/fgi/nextflow_many_files"
