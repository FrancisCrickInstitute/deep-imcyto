/*
 * STEP 1: imctools
 */

process IMCTOOLS {

    tag "$name"
    // label 'process_medium'
    publishDir "${params.outdir}/imctools/${name}", mode: params.publish_dir_mode,
        saveAs: { filename ->
                      if (filename.indexOf("version.txt") > 0) null
                      else filename
                }

    input:
    tuple val(name), path(mcd) //from ch_mcd
    path metadata //from ch_metadata

    output:
    tuple val(name), path("*/full_stack/*"), emit: ch_full_stack_tiff
    tuple val(name), path("*/ilastik_stack/*"), emit: ch_ilastik_stack_tiff
    tuple val(name), path("*/full_stack/191Ir_DNA1.tiff"), emit: ch_dna1
    tuple val(name), path("*/full_stack/193Ir_DNA2.tiff"), emit: ch_dna2
    tuple val(name), path("*/full_stack/100Ru_ruthenium.tiff"), emit: ch_Ru
    tuple val(name), path("*/full_stack"), emit: ch_full_stack_dir
    path "*/*ome.tiff", emit: ch_ome_tiff
    path "*.csv"
    path "*version.txt", emit: ch_imctools_version
    val "${params.outdir}/imctools", emit: ch_imctoolsdir

    script: // This script is bundled with the pipeline, in nf-core/imcyto/bin/
    """
    run_imctools.py $mcd $metadata
    pip show imctools | grep "Version" > imctools_version.txt
    """
}