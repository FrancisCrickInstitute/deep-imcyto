include {IMCTOOLS; IMCTOOLS_GEN; CORRECT_SPILLOVER; REMOVE_HOTPIXELS; GENERATE_METADATA; ADJUST_CHANNELS_QC} from '../modules/preprocessing.nf'
include { PREPROCESS_FULL_STACK } from '../modules/cellprofiler_pp_seg.nf'
include {group_fullstack} from '../lib/core_functions.nf'

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
            imctools_input = GENERATE_METADATA.out.mcd_metadata_tuple
            imctools_input.view()
            IMCTOOLS_GEN(imctools_input)
            ch_full_stack_dir = group_fullstack(IMCTOOLS_GEN.out.ch_full_stack_dir)
        }
        else {
            IMCTOOLS(mcd, metadata)
            ch_full_stack_dir = group_fullstack(IMCTOOLS.out.ch_full_stack_dir)
        }

        ADJUST_CHANNELS_QC(ch_full_stack_dir)


}