#!/bin/bash
#SBATCH --job-name=snakemake_test
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
module load snakemake

snakemake -n
