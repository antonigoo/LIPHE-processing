# Snakemake
There are two versions of this workflow:
- `Snakefile`: the regular one, in which snakemake is run locally, inside a batch job 
- `Snakefile_SLURM`: in which snakemake is going to submit rules as jobs to the slurm scheduler

## Running workflow
```bash
sbatch batchjob.sh
```

## Create DAG
In a terminal:
```bash
module load snakemake
snakemake -np --config BASE_PATH="/scratch/project_2008498/antongoo/fgi/snakemake_many_files"  --dag | dot -Tpng > dag.png
```

## Create a report
```bash
module load snakemake
export PATH="/projappl/project_2003180/samantha/bin:$PATH"export PATH="/projappl/project_2003180/samantha/bin:$PATH"
snakemake --report report.html --config BASE_PATH="/scratch/project_2008498/antongoo/fgi/snakemake_many_files"
```

## SLURM integraion
```bash
snakemake --keep-going -s Snakefile_SLURM -F --jobs 4 --executor slurm --default-resources slurm_account=project_2008498 slurm_partition=small --config BASE_PATH="/scratch/project_2008498/antongoo/fgi/snakemake_many_files"
```

## Hyperqueue integration
For hyperqueue integration, we need to set up the server, environment and directories. After that, we run snakeamke with generic cluster executor, and we provide submitting command. This approach will work with any other scheduler that does not have dedicated snakemake plugin. Set up and commands are taken from: https://docs.csc.fi/apps/hyperqueue/.
```bash
module load hyperqueue
export HQ_SERVER_DIR="$PWD/hq-server/$SLURM_JOB_ID"
mkdir -p "$HQ_SERVER_DIR"
hq server start & until hq job list &> /dev/null ; do sleep 1 ; done

srun --overlap --cpu-bind=none --mpi=none hq worker start \
    --manager slurm \
    --on-server-lost finish-running \
    --cpus="$SLURM_CPUS_PER_TASK" & hq worker wait 1

snakemake --keep-going -s Snakefile_SLURM --jobs 4 --executor cluster-generic --cluster-generic-submit-cmd "hq submit --cpus 1" --config BASE_PATH="/scratch/project_2008498/antongoo/fgi/snakemake_many_files"
```