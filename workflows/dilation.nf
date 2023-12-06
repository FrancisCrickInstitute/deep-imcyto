include { NUCLEAR_PREPROCESS; NUCLEAR_SEGMENTATION } from '../modules/nuclear_segmentation.nf'
include { NUCLEAR_DILATION; DILATION_MEASURE; DILATION_MEASURE as CELL_MEASURE } from '../modules/nuclear_dilation.nf'
include { PREPROCESS_FULL_STACK } from '../modules/cellprofiler_pp_seg.nf'
include {PSEUDO_HE } from '../modules/pseudo_HE.nf'
include {flatten_tiff ; get_roi_tuple; get_fullstack_tuple; group_channel; group_fullstack} from '../lib/core_functions.nf'
include {IMCTOOLS; IMCTOOLS_GEN; CORRECT_SPILLOVER; REMOVE_HOTPIXELS; GENERATE_METADATA} from '../modules/preprocessing.nf'
include {NoCompNoPreprocess; NoCompHotPixel; NoCompCP; CompHotPixel; CompNoPreprocess} from '../subworkflows/preprocessing_sub.nf'

workflow DILATION_WF {

    /*
    * ---------------------------------------------------------------------------------------------------------------------
    * Workflow to segment IMC images through an expansion of deep learning based nuclear predictions.
    *
    * -- Produces a segmentation of the nucleus and a segmentation of the cytoplasm based on an n-pixel dilation of the nucleus.
    * -- Measures a minimal set of nuclear and cellular parameters which can be used as input for TYPEx phenotyping, including 
    *    the mean intensity per cell.
    * ----------------------------------------------------------------------------------------------------------------------
    */

    take:
        mcd
        metadata
        weights
        compensation
        cppipe
        plugins
    

    main:

        if (params.generate_metadata == true) {
            GENERATE_METADATA(mcd)
            imctools_input = GENERATE_METADATA.out.mcd_metadata_tuple
            IMCTOOLS_GEN(imctools_input)
            // Group full stack files by sample and roi_id
            ch_full_stack_mapped_tiff = group_channel(IMCTOOLS_GEN.out.ch_full_stack_tiff)
            ch_dna_stack = group_channel(IMCTOOLS_GEN.out.ch_dna_stack_tiff)
            ch_dna_stack = ch_dna_stack.flatten().collate( 4 )
            ch_counterstain_dir = group_fullstack(IMCTOOLS_GEN.out.ch_counterstain_dir)
            ch_full_stack_dir = group_fullstack(IMCTOOLS_GEN.out.ch_full_stack_dir)
            ch_counterstain_dir = group_fullstack(IMCTOOLS_GEN.out.ch_counterstain_dir)
            metadata = GENERATE_METADATA.out.mcd_metadata_tuple
        }
        else {
            // Run IMC tools on raw files:
            IMCTOOLS(mcd, metadata)
            
            // Group full stack files by sample and roi_id
            ch_full_stack_mapped_tiff = group_channel(IMCTOOLS.out.ch_full_stack_tiff)
            ch_dna_stack = group_channel(IMCTOOLS.out.ch_dna_stack_tiff)
            ch_dna_stack = ch_dna_stack.flatten().collate( 4 )
            ch_counterstain_dir = group_fullstack(IMCTOOLS.out.ch_counterstain_dir)
            ch_full_stack_dir = group_fullstack(IMCTOOLS.out.ch_full_stack_dir)
            ch_counterstain_dir = group_fullstack(IMCTOOLS.out.ch_counterstain_dir)

        }

        if (params.compensation_tiff != false) {

            /*
            * Perform spillover correction:
            */

            // preprocess compensated channels with desired method:
            if (params.preprocess_method == 'cellprofiler') {
                { exit 1, "Cellprofiler preprocessing method not implemented. Please use 'hotpixel' or 'none'." }
                // CompCP
                // PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe, plugins) // Preprocess channels with a specified cppipe:
            }
            else if (params.preprocess_method == 'hotpixel') {
                if params.generate_metadata == true {
                    metadata = metadata.map { it[-1] }.first()
                    metadata.view()
                    CompHotPixel(ch_full_stack_dir, ch_dna_stack, ch_counterstain_dir, weights, metadata)
                }
                else {
                    CompHotPixel(ch_full_stack_dir, ch_dna_stack, ch_counterstain_dir, weights, metadata)
                }
            }
            else if (params.preprocess_method == 'none') {
                if params.generate_metadata == true {
                    metadata = metadata.map { it[-1] }.first()
                    metadata.view()
                    CompNoPreprocess(ch_full_stack_dir, ch_dna_stack, ch_counterstain_dir, weights, metadata)
                }
                else {
                    CompNoPreprocess(ch_full_stack_dir, ch_dna_stack, ch_counterstain_dir, weights, metadata)
                }
            }
            else { exit 1, "IMC channel preprocessing method not recognised!" }
            
        }

        else {

            /*
            * Do not perform spillover correction and preprocess uncompensated channels with desired method:
            */
            if (params.preprocess_method == 'cellprofiler') {
                NoCompCP(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe, plugins)
            }
            else if (params.preprocess_method == 'hotpixel') {
                NoCompHotPixel(ch_full_stack_dir, ch_dna_stack, ch_counterstain_dir, weights, metadata)
            }
            else if (params.preprocess_method == 'none') {
                NoCompNoPreprocess(ch_full_stack_dir, ch_dna_stack, ch_counterstain_dir, weights)
            }
            else { exit 1, "IMC channel preprocessing method not recognised!" }
        }

}