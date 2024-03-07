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

outputs: []

baseCommand: [python3, /projappl/project_2008498/code/workflow/01/01_add_parameters_and_normalize.py]
