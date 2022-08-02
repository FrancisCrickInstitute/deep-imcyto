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