# Toil

## Local run
```bash
export PATH="/projappl/project_2003180/samantha/bin:$PATH"
toil-wdl-runner workflow.wdl wdl-liphe.json --workDir /scratch/project_2008498/antongoo/fgi/toil_scratch
toil-cwl-runner workflow.cwl workflow.yaml --workDir /scratch/project_2008498/antongoo/fgi/toil_scratch
toil-cwl-runner 01_normalize.cwl 01_normalize.json --workDir /scratch/project_2008498/antongoo/fgi/toil_scratch
```
