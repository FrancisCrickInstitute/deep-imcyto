process PSEUDO_HE{
    /*
    * Make a pseudo-he image for each mcd file.
    */
    tag "${name}.${roi}"

    label 'deep_imcyto_local'

    publishDir "${params.outdir}/pseudo_HandE", mode: params.publish_dir_mode

    input:
    tuple val(name), val(roi), path(dna1), path(dna2)
    tuple val(name), val(roi), path(ruth)

    output:
    path "*.png", emit: ch_pseudos
    

    script:

    """
    makeHE.py -dna1 $dna1 -dna2 $dna2 --counterstain_dir $ruth --outdir ./ --imagename '$name-$roi'
    """

}


