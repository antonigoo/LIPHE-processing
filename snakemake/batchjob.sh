#!/bin/bash
#SBATCH --job-name=snakemake_test
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=40GB
#SBATCH --partition=interactive
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

module -q purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

snakemake --cores 1 fine_segmentation
