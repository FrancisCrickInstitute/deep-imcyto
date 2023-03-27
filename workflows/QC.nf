include {IMCTOOLS; CORRECT_SPILLOVER; REMOVE_HOTPIXELS; GENERATE_METADATA} from '../modules/preprocessing.nf'
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
            // Generate metadata if not explicitely provided:
        if (params.generate_metadata == true) {
            GENERATE_METADATA(mcd)
            metadata = GENERATE_METADATA.out.metadata.first()
        }

        IMCTOOLS(mcd, metadata)

}