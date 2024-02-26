task add_parameters_and_normalize {
  File input_las
  File output_las

  command <<<
    python ../workflow/01/01_add_parameters_and_normalize.py ${input_las} ${output_las}
  >>>
}

workflow MyWorkflow {
  File input_file
  File final_output_file

  call add_parameters_and_normalize {
    input: input_las=input_file
    output: output_las=final_output_file
  }
}
