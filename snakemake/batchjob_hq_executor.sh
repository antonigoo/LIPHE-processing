#!/bin/bash
#SBATCH --job-name=snakemake_hq
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=3
#SBATCH --mem-per-cpu=40GB
#SBATCH --partition=small
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

module load hyperqueue
export HQ_SERVER_DIR="$PWD/hq-server/$SLURM_JOB_ID"
mkdir -p "$HQ_SERVER_DIR"
hq server start & until hq job list &> /dev/null ; do sleep 1 ; done

srun --overlap --cpu-bind=none --mpi=none hq worker start \
    --manager slurm \
    --on-server-lost finish-running \
    --cpus="$SLURM_CPUS_PER_TASK" & hq worker wait 1

snakemake --keep-going -s Snakefile_SLURM --jobs 4 --executor cluster-generic --cluster-generic-submit-cmd "hq submit --cpus 1" --config BASE_PATH="/scratch/project_2008498/antongoo/fgi/snakemake_many_files"
