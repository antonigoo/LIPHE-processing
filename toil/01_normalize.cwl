cwlVersion: v1.2
class: CommandLineTool

inputs:
  input_las:
    type: File
    inputBinding:
      position: 1
  output_las:
    type: File
    inputBinding:
      position: 2

outputs:
  normalized_las: "/scratch/project_2008498/antongoo/fgi/toil/output/200406_100502_Sample_resample005__normalize.laz"

baseCommand: [python3, /projappl/project_2008498/code/workflow/01/01_add_parameters_and_normalize.py]
