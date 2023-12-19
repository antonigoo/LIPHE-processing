#!/bin/bash
#SBATCH --job-name=snakemake_test
#SBATCH --account=project_2008498
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=20GB
#SBATCH --partition=interactive
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

module purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"
module load snakemake

snakemake --cores 1 -np /scratch/project_2008498/antongoo/fgi/snakemake/output/200406_100502_Sample_resample0.05__normalized.las
