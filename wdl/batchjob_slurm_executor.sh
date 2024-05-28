#!/bin/bash
#SBATCH --job-name=cromwell_slurm
#SBATCH --account=project_2008498
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=3
#SBATCH --mem-per-cpu=40GB
#SBATCH --partition=small
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

module load biojava/11
export PATH="/projappl/project_2003180/samantha/bin:$PATH"
cd wdl

java -DLOG_LEVEL=INFO -Dconfig.file=slurmconf.conf  -jar cromwell-86.jar run workflow-slurm.wdl --inputs workflow-input.json --options options.json
