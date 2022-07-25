include { IMCTOOLS } from '../modules/imctools.nf'
include { PREPROCESS_FULL_STACK } from '../modules/cellprofiler_pp_seg.nf'

workflow MCD_QC {

    /*
    * Simple workflow to extract the raw tiff files from an MCD for the 
    * purposes of assessment of signal and other quality control tasks.
    */

    take:
    mcd
    metadata

    // Run imctools:
    main:
    IMCTOOLS(mcd, metadata)

}