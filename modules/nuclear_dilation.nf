process NUCLEAR_DILATION {

    tag "${name}.${roi}"
    // label 'process_low'

    executor "slurm"
	time "1h"
	clusterOptions "--part=gpu --gres=gpu:1"

    publishDir "${params.outdir}/nuclear_dilation/${name}/${roi}", mode: params.publish_dir_mode

    module params.md_conda
    conda params.dl_conda_env

    input:
    tuple val(name), val(roi), path(tiff), path(mask) //from ch_preprocess_full_stack_tiff_dilation

    output:
    path "*dilation.tiff", emit: ch_nuclear_dilation

    script:
    """
    echo tiff_files: ${tiff}
    echo mask_files: ${mask}
    nuclear_dilation.py --input_mask ${mask} --output_directory . --radius ${params.nuclear_dilation_radius} 
    """
}