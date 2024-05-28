#!/bin/bash
#SBATCH --job-name=snakemake_local
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=3
#SBATCH --mem-per-cpu=40GB
#SBATCH --partition=small
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

module -q purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH" 

snakemake --cores 1 --keep-going --config BASE_PATH="/scratch/project_2008498/antongoo/fgi/snakemake_many_files"
