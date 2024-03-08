# Example workflow
# Declare WDL version 1.0 if working in Terra
version 1.0

workflow LipheWorkflow {
    input {
        File input_las
        String cloud_name
    }

    call add_parameters_and_normalize { input: input_las = input_las, cloud_name = cloud_name }
    call georeference { input: input_las = add_parameters_and_normalize.normalized_las, cloud_name = cloud_name }
    call spatial_resample { input: input_las = georeference.georeference_las, cloud_name = cloud_name }
}

task add_parameters_and_normalize {
    input {
        File input_las
        String cloud_name
    }

    command <<<
        mkdir -p  ~{cloud_name}
        python /projappl/project_2008498/code/workflow/01/01_add_parameters_and_normalize.py ~{input_las} ~{cloud_name}/~{cloud_name}_normalized.las
    >>>

    output {
        File normalized_las = "${cloud_name}/${cloud_name}_normalized.las"
    }
}

task georeference {
    input {
        File input_las
        String cloud_name
    }

    command <<<
        mkdir -p  ~{cloud_name}
        python /projappl/project_2008498/code/workflow/02/02_georeference.py ~{input_las} ~{cloud_name}/~{cloud_name}_georeference.las
    >>>

    output {
        File georeference_las = "${cloud_name}/${cloud_name}_georeference.las"
    }
}

task spatial_resample {
    input {
        File input_las
        String cloud_name
    }

    command <<<
        mkdir -p  ~{cloud_name}
        python /projappl/project_2008498/code/workflow/03/03_spatial_resample.py ~{input_las} ~{cloud_name}/~{cloud_name}_resampled.las
    >>>

    output {
        File resampled_las = "${cloud_name}/${cloud_name}_resampled.las"
    }
}
