#!/usr/bin/env nextflow

params.base_path = System.getenv("BASE_PATH")

process findLazFiles {
    output:
    set file(file) into laz_files

    script:
    """
    find \${base_path} -type f -name '*.laz' | xargs -I {} basename {} .laz
    """
}

process generateTargetFiles {
    input:
    val file file

    output:
    set val(base_path) into target_files

    script:
    """
    filename=\${file}.out
    target=\${base_path}/output/\${file}/\${filename}
    echo \${target}
    """
}

workflow {
    laz_files = findLazFiles()
    target_files = generateTargetFiles(laz_files)

    base_name = file("${params.base_path}/output/{base_name}/{base_name}.out")

    addParametersAndNormalize base_name, from: laz_files
    georeference base_name, from: addParametersAndNormalize.out
    spatialResample base_name, from: georeference.out
    clippingTrees base_name, from: georeference.out
    normalizeToGround base_name, from: clippingTrees.out
    fineSegmentation base_name, from: normalizeToGround.out
    final base_name, from: fineSegmentation.out
}

process addParametersAndNormalize {
    input:
    val base_name

    output:
    val(base_path) into "${params.base_path}/output/{base_name}/{base_name}_normalized.las"

    script:
    """
    ../workflow/01/01_add_parameters_and_normalize.py
    """
}

process georeference {
    input:
    val base_name

    output:
    val(base_path) into "${params.base_path}/output/{base_name}/{base_name}_georef.las"

    script:
    """
    ../workflow/02/02_georeference.py
    """
}

process spatialResample {
    input:
    val base_name

    output:
    val(base_path) into "${params.base_path}/output/{base_name}/{base_name}_resampled.las"

    script:
    """
    ../workflow/03/03_spatial_resample.py
    """
}

process clippingTrees {
    input:
    val base_name

    output:
    directory val(base_path) into "${params.base_path}/output/{base_name}/single_trees/"

    script:
    """
    ../workflow/04/04_clipping_trees.py
    """
}

process normalizeToGround {
    input:
    val base_name

    output:
    directory val(base_path) into "${params.base_path}/output/{base_name}/single_trees_normalized_to_ground"

    script:
    """
    ../workflow/05/05_normalize_to_ground.py
    """
}

process fineSegmentation {
    input:
    val base_name

    output:
    directory val(output_dir) into "${params.base_path}/output/{base_name}/fine_segmentation"
    directory val(output_dir_noise) into "${params.base_path}/output/{base_name}/fine_segmentation_noise"

    script:
    """
    ../workflow/06/06_fine_segmentation.py
    """
}

process final {
    input:
    val base_name

    output:
    val(base_path) into "${params.base_path}/output/{base_name}/{base_name}.out"

    script:
    """
    echo "OK" > \${output}
    """
}
