#!/bin/bash
#SBATCH --job-name=nextflow_hq
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=3
#SBATCH --mem-per-cpu=20G
#SBATCH --partition=small

module load nextflow
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

module load hyperqueue
export HQ_SERVER_DIR="$PWD/hq-server/$SLURM_JOB_ID"
mkdir -p "$HQ_SERVER_DIR"
hq server start & until hq job list &> /dev/null ; do sleep 1 ; done

srun --overlap --cpu-bind=none --mpi=none hq worker start \
    --manager slurm \
    --on-server-lost finish-running \
    --cpus="$SLURM_CPUS_PER_TASK" & hq worker wait 1

module load nextflow
export PATH="/projappl/project_2003180/samantha/bin:$PATH"

nextflow run workflow.nf -c hyperqueue.config --base_path "/scratch/project_2008498/antongoo/fgi/nextflow_many_files" 

hq job wait all
hq worker stop all
hq server stop
