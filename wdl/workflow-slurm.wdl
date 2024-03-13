version 1.0

workflow LipheWorkflow {
    input {
        String input_directory
        String script_directory
    }
    
    call find_laz_files { input: input_directory = input_directory }
    scatter (input_las in find_laz_files.out) {
        String cloud_name = basename(input_las, ".laz")

        call add_parameters_and_normalize { input: input_las = input_las, cloud_name = cloud_name, script_path = script_directory }
        call georeference { input: input_las = add_parameters_and_normalize.out, cloud_name = cloud_name, script_path = script_directory }
        call spatial_resample { input: input_las = georeference.out, cloud_name = cloud_name, script_path = script_directory }
        call clipping_trees { input: input_las = spatial_resample.out, cloud_name = cloud_name, script_path = script_directory }
        call normalize_to_ground { input: input_dir = clipping_trees.out, cloud_name = cloud_name, script_path = script_directory }
        call fine_segmentation { input: input_dir = normalize_to_ground.out, cloud_name = cloud_name, script_path = script_directory }
    }
}

task find_laz_files {
    input {
        String input_directory
    }

    runtime { mem_per_cpu: "512MB" }

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
        String script_path
    }

    runtime { mem_per_cpu: "20GB" }

    command <<<
        mkdir -p ~{cloud_name}
        python ~{script_path}/01/01_add_parameters_and_normalize.py ~{input_las} ~{cloud_name}/~{cloud_name}_normalized.las
    >>>

    output {
        File out = "${cloud_name}/${cloud_name}_normalized.las"
    }
}

task georeference {
    input {
        File input_las
        String cloud_name
        String script_path
    }

    runtime { mem_per_cpu: "20GB" }

    command <<<
        mkdir -p ~{cloud_name}
        python ~{script_path}/02/02_georeference.py ~{input_las} ~{cloud_name}/~{cloud_name}_georeference.las
    >>>

    output {
        File out = "${cloud_name}/${cloud_name}_georeference.las"
    }
}

task spatial_resample {
    input {
        File input_las
        String cloud_name
        String script_path
    }

    runtime { mem_per_cpu: "20GB" }

    command <<<
        mkdir -p  ~{cloud_name}
        python ~{script_path}/03/03_spatial_resample.py ~{input_las} ~{cloud_name}/~{cloud_name}_resampled.las
    >>>

    output {
        File out = "${cloud_name}/${cloud_name}_resampled.las"
    }
}

task clipping_trees {
    input {
        File input_las
        String cloud_name
        String script_path
    }

    runtime { mem_per_cpu: "20GB" }

    command <<<
        mkdir -p ~{cloud_name}/single_trees
        python ~{script_path}/04/04_clipping_trees.py ~{input_las} ~{cloud_name}/single_trees/
    >>>

    output {
        # glob does work, but it puts the files into some weird directory, which is then copied to the scratch
        # I just use directory as File type
        File out = "${cloud_name}/single_trees/"
    }
}

task normalize_to_ground {
    input {
        File input_dir
        String cloud_name
        String script_path
    }

    runtime { mem_per_cpu: "30GB" }

    command <<<
        mkdir -p ~{cloud_name}/single_trees_normalized_to_ground
        python ~{script_path}/05/05_normalize_to_ground.py ~{input_dir} ~{cloud_name}/single_trees_normalized_to_ground/
    >>>

    output {
        File out = "${cloud_name}/single_trees_normalized_to_ground/"
    }
}

task fine_segmentation {
    input {
        File input_dir
        String cloud_name
        String script_path
    }

    runtime { 
        mem_per_cpu: "40GB"
        time: "00:05:00"
    }

    command <<<
        mkdir -p ~{cloud_name}/fine_segmentation
        mkdir -p ~{cloud_name}/fine_segmentation_noise
        python ~{script_path}/06/06_fine_segmentation.py ~{input_dir} ~{cloud_name}/fine_segmentation/ ~{cloud_name}/fine_segmentation_noise/
    >>>

    output {
        File out = "${cloud_name}/fine_segmentation/"
        File out_noise = "${cloud_name}/fine_segmentation_noise/"
    }
}
