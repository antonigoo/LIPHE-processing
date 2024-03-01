cwlVersion: v1.2
class: Workflow
label: Liphe workflow

requirements:
  InlineJavascriptRequirement: {}

inputs:
  input_las:
    type: File

outputs:
  out:
    type: File
    outputSource: 01_normalize/normalized_las

steps:
  01_normalize:
    run: 01_normalize.cwl
    in:
      input_las: input_las
      output_las: "${inputs.input_las.dirname}/output/${inputs.input_las.basename}_normalized.las"
    out: [normalized_las]
