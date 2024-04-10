#!/bin/bash
#SBATCH --job-name=snakemake_test
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=60GB
#SBATCH --partition=small
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

module -q purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

snakemake --cores 3 --keep-going --config BASE_PATH="/scratch/project_2008498/antongoo/fgi/snakemake_many_files"
# snakemake -s Snakefile_SLURM --keep-going  --jobs 4 --executor slurm --default-resources slurm_account=project_2008498 slurm_partition=small  --config BASE_PATH="/scratch/project_2008498/antongoo/fgi/snakemake_many_files"
