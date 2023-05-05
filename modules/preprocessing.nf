/*
 * STEP 1: imctools
 */

process GENERATE_METADATA {
    /*
    * Generate metadata file.
    */

    tag "$name"
    label 'deep_imcyto_CPU'

    publishDir "${params.outdir}/deep-imcyto/${params.release}/imctools/${name}", mode: params.publish_dir_mode

    input:
        tuple val(name), path(mcd)

    output:
        tuple val(name), path(mcd), path('metadata.csv'), emit: mcd_metadata_tuple
        path '*.csv'

    script:
        """
        autogenerate_deep-imcyto_metadata.py --imc_img $mcd --outdir .
        """
}

process IMCTOOLS {

    tag "$name"
    label "process_low" // 'process_medium'


    publishDir "${params.outdir}/deep-imcyto/${params.release}/imctools/${name}", mode: params.publish_dir_mode,
        saveAs: { filename ->
                      if (filename.indexOf("version.txt") > 0) null
                      else if (filename.endsWith(".ome.tiff") && (params.save_all_stacks == false)) null
                      else if (filename.contains("spillover") && (params.save_all_stacks == false)) null
                      else if (filename.contains("nuclear") && (params.save_all_stacks == false)) null
                      else if (filename.contains("counterstain") && (params.save_all_stacks == false)) null
                      else filename
                }

    input:
        tuple val(name), path(mcd) //from ch_mcd
        path metadata //from ch_metadata

    output:
        tuple val(name), path("*/full_stack/*"), emit: ch_full_stack_tiff
        tuple val(name), path("*/mccs_stack/*"), emit: ch_mccs_stack_tiff, optional: true
        tuple val(name), path("*/nuclear/*"), emit: ch_dna_stack_tiff, optional: true
        tuple val(name), path("*/spillover/*"), emit: ch_spillover_stack_tiff, optional: true
        tuple val(name), path("*/full_stack/191Ir_DNA1.tiff"), emit: ch_dna1, optional: true
        tuple val(name), path("*/full_stack/193Ir_DNA2.tiff"), emit: ch_dna2, optional: true
        tuple val(name), path("*/full_stack/100Ru_ruthenium.tiff"), emit: ch_Ru, optional: true
        tuple val(name), path("*/counterstain"), emit: ch_counterstain_dir, optional: true
        tuple val(name), path("*/full_stack"), emit: ch_full_stack_dir
        path "*/*ome.tiff", emit: ch_ome_tiff
        path "*.csv"
        path "*version.txt", emit: ch_imctools_version
        val "${params.outdir}/imctools", emit: ch_imctoolsdir

    script: // This script is bundled with the pipeline, in nf-core/imcyto/bin/
        """
        run_imctools.py $mcd $metadata ${params.save_all_stacks}
        pip show imctools | grep "Version" > imctools_version.txt
        """
}


process IMCTOOLS_GEN {

    tag "$name"
    label "process_low" // 'process_medium'


    publishDir "${params.outdir}/deep-imcyto/${params.release}/imctools/${name}", mode: params.publish_dir_mode,
        saveAs: { filename ->
                      if (filename.indexOf("version.txt") > 0) null
                      else if (filename.endsWith(".ome.tiff") && (params.save_all_stacks == false)) null
                      else if (filename.contains("spillover") && (params.save_all_stacks == false)) null
                      else if (filename.contains("nuclear") && (params.save_all_stacks == false)) null
                      else if (filename.contains("counterstain") && (params.save_all_stacks == false)) null
                      else filename
                }

    input:
        tuple val(name), path(mcd), path(metadata) //from ch_mcd

    output:
        tuple val(name), path("*/full_stack/*"), emit: ch_full_stack_tiff
        tuple val(name), path("*/mccs_stack/*"), emit: ch_mccs_stack_tiff, optional: true
        tuple val(name), path("*/nuclear/*"), emit: ch_dna_stack_tiff, optional: true
        tuple val(name), path("*/spillover/*"), emit: ch_spillover_stack_tiff, optional: true
        tuple val(name), path("*/full_stack/191Ir_DNA1.tiff"), emit: ch_dna1, optional: true
        tuple val(name), path("*/full_stack/193Ir_DNA2.tiff"), emit: ch_dna2, optional: true
        tuple val(name), path("*/full_stack/100Ru_ruthenium.tiff"), emit: ch_Ru, optional: true
        tuple val(name), path("*/counterstain"), emit: ch_counterstain_dir, optional: true
        tuple val(name), path("*/full_stack"), emit: ch_full_stack_dir
        path "*/*ome.tiff", emit: ch_ome_tiff
        path "*.csv"
        path "*version.txt", emit: ch_imctools_version
        val "${params.outdir}/imctools", emit: ch_imctoolsdir

    script: // This script is bundled with the pipeline, in nf-core/imcyto/bin/
        """
        run_imctools.py $mcd $metadata ${params.save_all_stacks}
        pip show imctools | grep "Version" > imctools_version.txt
        """
}


process CORRECT_SPILLOVER{
    /*
    * Correct isotope spillover.
    */

    tag "$name-$roi"
    label "deep_imcyto_GPU"

    publishDir "${params.outdir}/deep-imcyto/${params.release}/channel_preprocessing/${name}/${roi}", mode: params.publish_dir_mode, enabled: params.save_all_stacks

    input:
        tuple val(name), val(roi), path(full_stack_dir)
        path metadata
    

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
    label "deep_imcyto_GPU"

    publishDir "${params.outdir}/deep-imcyto/${params.release}/channel_preprocessing/${name}/${roi}", mode: params.publish_dir_mode, enabled: params.save_all_stacks

    input:
        tuple val(name), val(roi), path(full_stack_dir)
        path metadata

    output:
        tuple val(name), val(roi), path("./hotpixel_removed/*.tiff"), emit: ch_hp_tiff, optional: true
        tuple val(name), path("./hotpixel_removed/*"), emit: ch_full_stack_tiff, optional: true
        tuple val(name), path("./hotpixel_removed/191Ir_DNA1.tiff"), emit: ch_dna1, optional: true
        tuple val(name), path("./hotpixel_removed/193Ir_DNA2.tiff"), emit: ch_dna2, optional: true
        tuple val(name), path("./hotpixel_removed/100Ru_ruthenium.tiff"), emit: ch_Ru, optional: true
        tuple val(name), path("./hotpixel_removed"), emit: ch_full_stack_dir, optional: true
        tuple val(name), val(roi), path("./hotpixel_removed"), emit: ch_hp_dir, optional: true

    script:
        """
        remove_hotpixels_channel.py --input_dir $full_stack_dir\
                                        --outdir './hotpixel_removed'\
                                        --filter_size 3\
                                        --hot_pixel_threshold 50\
                                        --file_extension '.tiff'
        """  
}

process ADJUST_CHANNELS_QC {


    tag "$name-$roi"

    publishDir "${params.outdir}/deep-imcyto/${params.release}/channel_preprocessing/${name}/${roi}", mode: params.publish_dir_mode

    input:
        tuple val(name), val(roi), path(full_stack_dir)

    output:
        tuple val(name), val(roi), path("*/*/*.png"), emit: ch_qc_pngs, optional: true

    script:
        """
        QC_adjust.py --input $full_stack_dir
        """  
}