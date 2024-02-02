#!/usr/bin/env nextflow

params.base_path = "/scratch/project_2008498/antongoo/fgi/nextflow"

process addParametersAndNormalize {
    publishDir "$params.base_path/output/$point_cloud.baseName", mode: 'copy', overwrite: false

    input:
    path point_cloud

    output:
    tuple path("${point_cloud.baseName}_normalized.las"), val(point_cloud.baseName)

    script:
    """
    $projectDir/01/01_add_parameters_and_normalize.py $point_cloud ${point_cloud.baseName}_normalized.las
    """
}

process georeference {
    publishDir "$params.base_path/output/$base_name", mode: 'copy', overwrite: false

    input:
    tuple path(point_cloud), val(base_name)

    output:
    tuple path("${base_name}_georeference.las"), val(base_name)

    script:
    """
    $projectDir/02/02_georeference.py $point_cloud ${base_name}_georeference.las
    """
}

process spatialResample {
    publishDir "$params.base_path/output/$base_name", mode: 'copy', overwrite: false

    input:
    tuple path(point_cloud), val(base_name)

    output:
    tuple path("${base_name}_resampled.las"), val(base_name)

    script:
    """
    $projectDir/03/03_spatial_resample.py $point_cloud ${base_name}_resampled.las
    """
}

process clippingTrees {
    publishDir "$params.base_path/output/$base_name", mode: 'copy', overwrite: false

    input:
    tuple path(point_cloud), val(base_name)

    output:
    tuple path("single_trees/${base_name}*.laz"), val(base_name)

    script:
    """
    mkdir -p single_trees
    $projectDir/04/04_clipping_trees.py $point_cloud ./single_trees/
    """
}

process normalizeToGround {
    publishDir "$params.base_path/output/$base_name", mode: 'copy', overwrite: false

    input:
    tuple path(point_clouds), val(base_name)

    output:
    tuple path("single_trees_normalized_to_ground/${base_name}*.laz"), val(base_name)

    script:
    """
    mkdir -p single_trees_normalized_to_ground
    $projectDir/05/05_normalize_to_ground.py ./ ./single_trees_normalized_to_ground/
    """
}

process fineSegmentation {
    publishDir "$params.base_path/output/$base_name", mode: 'copy', overwrite: false

    input:
    tuple path(point_clouds), val(base_name)

    output:
    tuple path("fine_segmentation/${base_name}*.laz"), path("fine_segmentation_noise/${base_name}*.laz")

    script:
    """
    mkdir -p fine_segmentation
    mkdir -p fine_segmentation_noise
    $projectDir/06/06_fine_segmentation.py ./ ./fine_segmentation/ ./fine_segmentation_noise/
    """
}

workflow {
    Channel.fromPath("$params.base_path/*.laz")
     | addParametersAndNormalize 
     | georeference 
     | spatialResample
     | clippingTrees
     | normalizeToGround
     | fineSegmentation
}
