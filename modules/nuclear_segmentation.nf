/*
 * Nuclear image preprocessing.
 */

process NUCLEAR_PREPROCESS {

    tag "${name}.${roi}"

    // executor "slurm"
	// time "1h"
	// clusterOptions "--part=gpu --gres=gpu:1"

    module params.md_conda
    conda params.dl_conda_env

    publishDir "${params.outdir}/nuclear_preprocess", mode: params.publish_dir_mode, overwrite: true

    input:
    tuple val(name), val(roi), path(dna1)
    tuple val(name), val(roi), path(dna2)

    output:
    tuple val(name), val(roi), path("*.png"), emit: ch_preprocessed_nuclei
    
    script:
    """
    unet_preprocess.py --dna1 $dna1 --dna2 $dna2 --outdir . --imagename '$name-$roi'
    """

}

/*
 * Nuclear segmentation.
 */

process NUCLEAR_SEGMENTATION {

    tag "${name}.${roi}"

    executor "slurm"
	time "1h"
	clusterOptions "--part=gpu --gres=gpu:1"

    module params.md_conda
    conda params.dl_conda_env

    publishDir "${params.outdir}/nuclear_segmentation", mode: params.publish_dir_mode, overwrite: true
 
    input:
    tuple val(name), val(roi), path(preprocessed_image) //from ch_preprocess_results
    val weights //from ch_nuclear_weights

    output:
    val "${params.outdir}/nuclear_segmentation", emit: ch_nuc_seg_results
    val true, emit: ch_proceed_cell_segmentation
    val true, emit: ch_proceed_dilation
    tuple val(name), val(roi), path("postprocess_predictions/*.tiff"), emit: ch_nuclear_predictions
    path "*/*/*.tiff"
    path "*/*/*.png"
 
    """
    predict.py --image $preprocessed_image --outdir . --weights $weights
    """
}