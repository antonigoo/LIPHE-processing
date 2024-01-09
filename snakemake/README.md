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