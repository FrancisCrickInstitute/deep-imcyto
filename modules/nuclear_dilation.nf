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
        tuple val(name), val(roi), path(mask) //from ch_preprocess_full_stack_tiff_dilation

    output:
        tuple val(name), val(roi), path("*dilation.tiff"), emit: ch_nuclear_dilation

    script:
        """
        nuclear_dilation.py --input_mask ${mask} --output_directory . --radius ${params.nuclear_dilation_radius} 
        """
}

process DILATION_MEASURE {

    tag "${name}.${roi}"
    // label 'process_low'
    executor "slurm"
    time "1h"
    clusterOptions "--part=gpu --gres=gpu:1"
    
    publishDir "${params.outdir}/nuclear_dilation/${name}/${roi}", mode: params.publish_dir_mode
    
    module params.md_conda
    conda params.dl_conda_env
    
    input:
        tuple val(name), val(roi), path(stack_dir), path(cellmask) //from ch_preprocess_full_stack_tiff_dilation
        val outfile
    
    output:
        path "*.csv"
    
    script:
        """
        simple_seg_measurement.py --input_dir ${stack_dir} --output_dir . --label_image_path ${cellmask} --output_file ${outfile}
        """        
}

process OVERLAYS {
    /*
    * Make a pseudo-he image for each mcd file.
    */
    tag "${name}.${roi}"

    publishDir "${params.outdir}/nuclear_dilation/${name}/${roi}", mode: params.publish_dir_mode

    input:
    tuple val(name), val(roi), path(overlay_image), path(nuc_mask), path(cell_mask) // from ch_preprocessed_nuclei
    // tuple val(name), val(roi), path(nuc_mask), emit: ch_nuclear_predictions
    // tuple val(name), val(roi), path(cell_mask), emit: ch_nuclear_dilation

    output:
    path "*.png", emit: ch_overlays
    

    script:

    """
    overlays.py --nuclear_segmentation ${nuc_mask} --cell_segmentation ${cell_mask} --image ${overlay_image} --outdir . --imagename '$name-$roi'
    """

}