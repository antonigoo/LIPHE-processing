#!/usr/bin/env nextflow

params.base_path = "/scratch/project_2008498/antongoo/fgi/nextflow"
// params.base_name = "200406_100502_Sample_resample005"
project_dir = projectDir

process addParametersAndNormalize {
    publishDir "$params.base_path/output"

    input:
    path point_cloud

    output:
    path "${point_cloud.baseName}_normalized.las"

    script:
    """
    $projectDir/01/01_add_parameters_and_normalize.py ${params.base_path + '/' + point_cloud.name} ${point_cloud.baseName}_normalized.las
    """
}

process georeference {
    publishDir "$params.base_path/output"

    input:
    path point_cloud

    output:
    path "${point_cloud.baseName.split("_").dropRight(1).join("_")}_georeference.las"

    script:
    """
    $projectDir/02/02_georeference.py $point_cloud ${point_cloud.baseName.split("_").dropRight(1).join("_")}_georeference.las
    """
}

process spatialResample {
    publishDir "$params.base_path/output"

    input:
    path point_cloud

    output:
    path "${point_cloud.baseName.split("_").dropRight(1).join("_")}_resampled.las"

    script:
    """
    $projectDir/03/03_spatial_resample.py $point_cloud ${point_cloud.baseName.split("_").dropRight(1).join("_")}_resampled.las
    """
}

workflow {
    Channel.fromPath("$params.base_path/*.laz")
     | addParametersAndNormalize 
     | georeference 
     | spatialResample
}
