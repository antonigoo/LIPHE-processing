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
java -DLOG_LEVEL=INFO  -jar cromwell-86.jar run workflow.wdl --inputs workflow-input.json 
```

