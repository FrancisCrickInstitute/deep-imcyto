/*
 * Nuclear image preprocessing.
 */

process NUCLEAR_PREPROCESS {

    // executor "slurm"
	// time "1h"
	// clusterOptions "--part=gpu --gres=gpu:1"

    module params.md_conda
    conda params.dl_conda_env

    publishDir "${params.outdir}/nuclear_preprocess", mode: params.publish_dir_mode, overwrite: true

    input:
    val indir
    val preprocessdir //from ch_imctoolsdir
    // val preprocessdir //from ch_nuclear_ppdir

    output:
    val preprocessdir, emit: ch_preprocess_results
    
    script:
    """
    echo $indir
    echo $preprocessdir
    unet_preprocess.py $indir $preprocessdir
    """

}

/*
 * Nuclear segmentation.
 */

process NUCLEAR_SEGMENTATION {

    executor "slurm"
	time "1h"
	clusterOptions "--part=gpu --gres=gpu:1"

    module params.md_conda
    conda params.dl_conda_env

    publishDir "${params.outdir}/nuclear_segmentation", mode: params.publish_dir_mode, overwrite: true
 
    input:
    val preprocessdir //from ch_preprocess_results
    val weights //from ch_nuclear_weights

    output:
    val "${params.outdir}/nuclear_segmentation", emit: ch_nuc_seg_results
    val true, emit: ch_proceed_cell_segmentation
    val true, emit: ch_proceed_dilation
    path "*/postprocess_predictions/*.tiff", emit: ch_nuclear_predictions
 
    """
    predict.py $preprocessdir . p1 all $weights
    """
}