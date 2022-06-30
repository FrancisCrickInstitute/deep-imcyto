process PSEUDO_HE{
    /*
    * Make a pseudo-he image for each mcd file.
    */
    tag "${name}.${roi}"

    // executor "slurm"
	// time "5m"
	// clusterOptions "--part=gpu --gres=gpu:1"

    module params.md_conda
    conda params.dl_conda_env

    publishDir "${params.outdir}/pseudo_HandE", mode: params.publish_dir_mode

    input:
    tuple val(name), val(roi), path(dna1)
    tuple val(name), val(roi), path(dna2)
    tuple val(name), val(roi), path(ruth)

    output:
    path "*.png", emit: ch_pseudos
    

    script:

    """
    makeHE.py -dna1 $dna1 -dna2 $dna2 -ruth $ruth --outdir ./ --imagename '$name-$roi'
    """

}