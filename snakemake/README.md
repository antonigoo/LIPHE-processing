# Snakemake
Configure workflow for your input file by changing variables in the `config.json` file.

## Running workflow
```bash
sbatch batchjob.sh
```

## Create DAG
In a terminal:
```bash
module load snakemake
snakemake -np --dag | dot -Tpng > dag.png
```

## SLURM integraion
```bash
snakemake -s Snakefile_SLURM -F fine_segmentation --jobs 1 --executor slurm --default-resources slurm_account=project_2008498 slurm_partition=interactive
```