#!/bin/bash
#SBATCH --account=project_2008498
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=20GB
#SBATCH --time=00:20:00

module purge
export PATH="/projappl/project_2003180/samantha/bin:$PATH"
module load biojava/11

module load hyperqueue
export HQ_SERVER_DIR="$PWD/hq-server/$SLURM_JOB_ID"
mkdir -p "$HQ_SERVER_DIR"
hq server start & until hq job list &> /dev/null ; do sleep 1 ; done

srun --overlap --cpu-bind=none --mpi=none hq worker start \
    --manager slurm \
    --on-server-lost finish-running \
    --cpus="$SLURM_CPUS_PER_TASK" & hq worker wait 1

java -DLOG_LEVEL=INFO -Dconfig.file=hqconf.conf  -jar cromwell-86.jar run workflow-slurm.wdl --inputs workflow-input.json --options options.json

hq job wait all
hq worker stop all
hq server stop