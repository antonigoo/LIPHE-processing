# LIPHE-processing - WDL

To install Cromwell, download `.jar` file from Cromwell github.
```bash
cd wdl
wget https://github.com/broadinstitute/cromwell/releases/download/86/cromwell-86.jar
```

### Local run
```bash
module load biojava/11
export PATH="/projappl/project_2003180/samantha/bin:$PATH"
cd wdl
java -DLOG_LEVEL=INFO  -Dconfig.file=basicconf.conf -jar cromwell-86.jar run workflow.wdl --inputs workflow-input.json --options options.json
```

### SLURM
You can modify the runtime parameters in `workflow-slurm.wdl`. If they are not specified, then the default (if exists) from `slurmconf.conf` will be used. In general, cromwell does not have any special slurm features built-in. As you can see in `slurmconf.conf`, we have to specify everything ourself (although this configuration was taken directly from cromwell documentation: https://cromwell.readthedocs.io/en/stable/backends/SLURM/).

You can set the maximum number of concurrent jobs using `concurrent-job-limit` option in `slurmconf.conf`.

Warning: if a job is killed by slurm, cromwell will not receive return code from a task. Cromwell needs return code to determine state of a task. This problem is handled by check-alive command (see `slurmconf.conf`), but it has some flaws, for example: https://github.com/broadinstitute/cromwell/issues/5400. If not configured correctly together with `exit-code-timeout-seconds` it can hang out the entire workflow.

```bash
module load biojava/11
export PATH="/projappl/project_2003180/samantha/bin:$PATH"
cd wdl
java -DLOG_LEVEL=INFO -Dconfig.file=slurmconf.conf  -jar cromwell-86.jar run workflow-slurm.wdl --inputs workflow-input.json --options options.json
```

### Hyperqueue
For hyperqueue integration, we need to set up the server, environment and directories. Set up and commands are taken from: https://docs.csc.fi/apps/hyperqueue/. Hyperqueue config file `hqconf.conf` was built by me. I modified the slurm example and by trial and error specified all necessary parameters. It has similar problem with the check-alive command.
```bash
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
```