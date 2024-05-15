# LIPHE-processing - Nextflow version

In this example, workflow definition file is located in workflow folder. The reason for that is because now, we can use `projectDir` variable for accessing our scripts. Nextflow is running process in a new folder in work directory, so it is hard to hardcode path to a file (the recommended behavior is to make you scripts accessible like any other command line tool).

## Preparing files
chmod +x or just rollback to python srcipt.py ... version

## Running locally
```bash
cd workflow
module purge
module load nextflow
export PATH="/projappl/project_2003180/samantha/bin:$PATH"
nextflow run workflow.nf --base_path "/scratch/project_2008498/antongoo/fgi/nextflow_many_files"
```

## Reports
```bash
nextflow run workflow.nf --base_path "/scratch/project_2008498/antongoo/fgi/nextflow_many_files" -with-dag flowchart.png
```

## Run the entire workflow in a batch file
See `workflow/batchjob.sh` for details.
```bash
sbatch batchjob.sh
```

## Slurm integration
This will create a slurm job for each process. The parameters for a job are specified globally in slurm.config, and they can be overwritten by values specified in the process definition. Set the maximum number of jobs in `slurm.config` 
```bash
module load nextflow
export PATH="/projappl/project_2003180/samantha/bin:$PATH"
nextflow run workflow.nf -c slurm.config --base_path "/scratch/project_2008498/antongoo/fgi/nextflow_many_files" 
```

## Hyperqueue integration
From version 22.05.0-edge: Hyperqueue integration is built-in into Nextflow. We can use `executor = "hyperqueue"`. Not that for older versions, instead of `executor = "hyperqueue"` we have to use `executor = "hq"`.
Set up and commands are taken from: https://docs.csc.fi/apps/hyperqueue/. Another configuration available here: https://docs.csc.fi/support/tutorials/nextflow-hq/.
```bash
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
```

