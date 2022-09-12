/*
 * STEP 1: imctools
 */

process IMCTOOLS {

    tag "$name"
    // label 'process_low' // 'process_medium'
    
    executor "local"
    // executor "slurm"
	// time "1h"
	// clusterOptions "--part=gpu --gres=gpu:1"

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
        tuple val(name), path("*/nuclear/*"), emit: ch_dna_stack_tiff, optional: true
        tuple val(name), path("*/spillover/*"), emit: ch_spillover_stack_tiff, optional: true
        // tuple val(name), path("*/full_stack/191Ir_DNA1.tiff"), emit: ch_dna1, optional: true
        // tuple val(name), path("*/full_stack/193Ir_DNA2.tiff"), emit: ch_dna2, optional: true
        tuple val(name), path("*/counterstain"), emit: ch_counterstain_dir, optional: true
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



process CORRECT_SPILLOVER {

    tag "$name-$roi"
    // label 'process_low' // 'process_medium'
    
    // executor "local"
    executor "slurm"
	time "1h"
	clusterOptions "--part=gpu --gres=gpu:1"

    publishDir "${params.outdir}/channel_preprocessing/${name}/${roi}", mode: params.publish_dir_mode

    input:
        tuple val(name), val(roi), path(full_stack_dir) //from ch_mcd
        path metadata //from ch_metadata
        // path sm

    output:
        tuple val(name), val(roi), path("./spillover_compensated/*.tiff"), emit: ch_spillover_comp_tiff, optional: true
        tuple val(name), path("./spillover_compensated/*"), emit: ch_full_stack_tiff, optional: true
        tuple val(name), path("./spillover_compensated/191Ir_DNA1.tiff"), emit: ch_dna1, optional: true
        tuple val(name), path("./spillover_compensated/193Ir_DNA2.tiff"), emit: ch_dna2, optional: true
        tuple val(name), path("./spillover_compensated/100Ru_ruthenium.tiff"), emit: ch_Ru, optional: true
        tuple val(name), val(roi), path("./spillover_compensated"), emit: ch_comp_stack_dir, optional: true

    script:
        """
        deepimcyto_correct_spillover.py --input $full_stack_dir\
                                        --outdir './spillover_compensated'\
                                        --extension '.tiff'\
                                        --spillover_matrix ${params.compensation_tiff}\
                                        --metadata ${params.metadata}\
                                        --method ${params.compensation_method}
        """

}

process REMOVE_HOTPIXELS {

    tag "$name-$roi"
    // label 'process_low' // 'process_medium'
    
    // executor "local"
    executor "slurm"
	time "1h"
	clusterOptions "--part=gpu --gres=gpu:1"

    publishDir "${params.outdir}/channel_preprocessing/${name}/${roi}", mode: params.publish_dir_mode

    input:
        tuple val(name), val(roi), path(full_stack_dir) //from ch_mcd
        path metadata //from ch_metadata

    output:
        tuple val(name), val(roi), path("./hotpixel_removed/*.tiff"), emit: ch_spillover_compensated_tiff, optional: true
        tuple val(name), path("./hotpixel_removed/*"), emit: ch_full_stack_tiff, optional: true
        tuple val(name), path("./hotpixel_removed/191Ir_DNA1.tiff"), emit: ch_dna1, optional: true
        tuple val(name), path("./hotpixel_removed/193Ir_DNA2.tiff"), emit: ch_dna2, optional: true
        tuple val(name), path("./hotpixel_removed/100Ru_ruthenium.tiff"), emit: ch_Ru, optional: true
        tuple val(name), path("./hotpixel_removed"), emit: ch_full_stack_dir, optional: true

    script:
        """
        remove_hotpixels_channel.py --input_dir $full_stack_dir\
                                        --outdir './hotpixel_removed'\
                                        --filter_size 3\
                                        --hot_pixel_threshold 50\
                                        --file_extension '.tiff'
        """  
}