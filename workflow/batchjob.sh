#!/bin/bash
#SBATCH --job-name=nextflow
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=200G
#SBATCH --partition=small

module purge
module load nextflow
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

nextflow run workflow.nf --base_path <value>
