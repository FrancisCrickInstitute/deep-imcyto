process NUCLEAR_DILATION {

    tag "${name}.${roi}"
    label 'deep_imcyto_GPU'

    publishDir "${params.outdir}/deep-imcyto/${params.release}/simple_segmentation/${name}/${roi}", mode: params.publish_dir_mode

    input:
        tuple val(name), val(roi), path(mask)

    output:
        tuple val(name), val(roi), path("*dilation.tiff"), emit: ch_nuclear_dilation

    script:
        """
        nuclear_dilation.py --input_mask ${mask} --output_directory . --radius ${params.nuclear_dilation_radius} 
        """
}

process DILATION_MEASURE {

    tag "${name}.${roi}"
    label 'deep_imcyto_GPU'
    
    publishDir "${params.outdir}/deep-imcyto/${params.release}/simple_segmentation/${name}/${roi}", mode: params.publish_dir_mode
    
    input:
        tuple val(name), val(roi), path(stack_dir), path(cellmask)
        val outfile
    
    output:
        path "*.csv"
        path "*.png"
    
    script:
        """
        simple_seg_measurement.py --input_dir ${stack_dir} --output_dir . --label_image_path ${cellmask} --output_file ${outfile} --n_neighbours ${params.n_neighbours}
        """        
}

process OVERLAYS {
    /*
    * Make a pseudo-he image for each mcd file.
    */
    tag "${name}.${roi}"
    label 'deep_imcyto_local'

    publishDir "${params.outdir}/deep-imcyto/${params.release}/simple_segmentation/${name}/${roi}", mode: params.publish_dir_mode

    input:
    tuple val(name), val(roi), path(overlay_image), path(nuc_mask), path(cell_mask)

    output:
    path "*.png", emit: ch_overlays
    

    script:

    """
    overlays.py --nuclear_segmentation ${nuc_mask} --cell_segmentation ${cell_mask} --image ${overlay_image} --outdir . --imagename '$name-$roi'
    """

}