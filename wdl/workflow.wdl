version 1.0

workflow LipheWorkflow {
    input {
        String input_directory
    }
    
    call find_laz_files { input: input_directory = input_directory }
    scatter (input_las in find_laz_files.out) {
        String cloud_name = basename(input_las, ".laz")

        call add_parameters_and_normalize { input: input_las = input_las, cloud_name = cloud_name }
        call georeference { input: input_las = add_parameters_and_normalize.out, cloud_name = cloud_name }
        # call spatial_resample { input: input_las = georeference.out, cloud_name = cloud_name }
        call clipping_trees { input: input_las = georeference.out, cloud_name = cloud_name }
        call normalize_to_ground { input: input_las_files = clipping_trees.out, cloud_name = cloud_name }
    }
}

task find_laz_files {
    input {
        String input_directory
    }

    command <<<
        find ~{input_directory} -maxdepth 1 -type f -name "*.laz"
    >>>

    output {
        Array[String] out = read_lines(stdout())
    }
}

task add_parameters_and_normalize {
    input {
        File input_las
        String cloud_name
    }

    command <<<
        mkdir -p ~{cloud_name}
        python /projappl/project_2008498/code/workflow/01/01_add_parameters_and_normalize.py ~{input_las} ~{cloud_name}/~{cloud_name}_normalized.las
    >>>

    output {
        File out = "${cloud_name}/${cloud_name}_normalized.las"
    }
}

task georeference {
    input {
        File input_las
        String cloud_name
    }

    command <<<
        mkdir -p ~{cloud_name}
        python /projappl/project_2008498/code/workflow/02/02_georeference.py ~{input_las} ~{cloud_name}/~{cloud_name}_georeference.las
    >>>

    output {
        File out = "${cloud_name}/${cloud_name}_georeference.las"
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
        File out = "${cloud_name}/${cloud_name}_resampled.las"
    }
}

task clipping_trees {
    input {
        File input_las
        String cloud_name
    }

    command <<<
        mkdir -p ~{cloud_name}/single_trees
        python /projappl/project_2008498/code/workflow/04/04_clipping_trees.py ~{input_las} ~{cloud_name}/single_trees/
        find ~{cloud_name}/single_trees -maxdepth 1 -type f -name "*.laz" > result.txt
    >>>

    output {
        # glob does work, but it puts the files into some weird directory, which is then copied to the scratch
        Array[File] out = read_lines("result.txt")
    }
}

task normalize_to_ground {
    input {
        Array[File] input_las_files
        String cloud_name
    }

    command <<<
        mkdir -p ~{cloud_name}/single_trees_normalized_to_ground
        python /projappl/project_2008498/code/workflow/05/05_normalize_to_ground.py ./ ~{cloud_name}/single_trees_normalized_to_ground/
        find ~{cloud_name}/single_trees_normalized_to_ground -maxdepth 1 -type f -name "*.laz" > result.txt
    >>>

    output {
        Array[File] out = read_lines("result.txt")
    }
}
