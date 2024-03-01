cwlVersion: v1.2
class: CommandLineTool

requirements:
  InlineJavascriptRequirement: {}

inputs:
  input_las: 
    type: File
    inputBinding:
      position: 1
  output_las:
    type: string
    inputBinding:
      position: 2

baseCommand: [python3, /projappl/project_2008498/code/workflow/01/01_add_parameters_and_normalize.py]

outputs:
  normalized_las:
    type: File
    outputBinding:
      glob: "${inputs.input_file.basename}_v2.txt"
