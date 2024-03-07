cwlVersion: v1.2
class: Workflow
label: Liphe workflow

inputs:
  input_las:
    type: File
  output_las:
    type: File

outputs: []

steps:
  01_normalize:
    run: 01_normalize.cwl
    in:
      input_las: input_las
      output_las: output_las
    out: []
