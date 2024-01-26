#!/usr/bin/env nextflow

params.base_path = "/scratch/project_2008498/antongoo/fgi/nextflow"


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

workflow {
    Channel.of("/scratch/project_2008498/antongoo/fgi/nextflow/200..._1.laz")
     | addParametersAndNormalize 
     | georeference 
     | spatialResample
}
