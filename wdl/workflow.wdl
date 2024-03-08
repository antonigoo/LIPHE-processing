# Example workflow
# Declare WDL version 1.0 if working in Terra
version 1.0

workflow LipheWorkflow {
    input {
        File input_las
        String cloud_name
    }

    call add_parameters_and_normalize {
        input: input_las = input_las, cloud_name = cloud_name
    }
}

task add_parameters_and_normalize {
    input {
        File input_las
        String cloud_name
    }

    command <<<
        python /projappl/project_2008498/code/workflow/01/01_add_parameters_and_normalize.py ~{input_las} ~{cloud_name}_normalized.laz
    >>>

    output {
        File normalized_las = "${cloud_name}_normalized.laz"
    }
}