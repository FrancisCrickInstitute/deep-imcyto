include { NUCLEAR_PREPROCESS; NUCLEAR_SEGMENTATION } from '../modules/nuclear_segmentation.nf'
include { NUCLEAR_DILATION; DILATION_MEASURE; DILATION_MEASURE as CELL_MEASURE } from '../modules/nuclear_dilation.nf'
include { PREPROCESS_FULL_STACK } from '../modules/cellprofiler_pp_seg.nf'
include {PSEUDO_HE } from '../modules/pseudo_HE.nf'
include {flatten_tiff ; get_roi_tuple; get_fullstack_tuple; group_channel; group_fullstack} from '../lib/core_functions.nf'
include {IMCTOOLS; CORRECT_SPILLOVER; REMOVE_HOTPIXELS} from '../modules/preprocessing.nf'

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
        
        //Run IMCTOOLS:
        IMCTOOLS(mcd, metadata)

        // Group full stack files by sample and roi_id:
        ch_full_stack_mapped_tiff = group_channel(IMCTOOLS.out.ch_full_stack_tiff)
        // ch_dna1 = group_channel(IMCTOOLS.out.ch_dna1)
        // ch_dna2 = group_channel(IMCTOOLS.out.ch_dna2)
        // ch_Ru = group_channel(IMCTOOLS.out.ch_Ru)
        ch_dna_stack = group_channel(IMCTOOLS.out.ch_dna_stack_tiff)
        ch_dna_stack = ch_dna_stack.flatten().collate( 4 ).view()
        ch_full_stack_dir = group_fullstack(IMCTOOLS.out.ch_full_stack_dir)
        ch_counterstain_dir = group_fullstack(IMCTOOLS.out.ch_counterstain_dir)

        // Perform spillover correction if required:
        if (params.compensation_tiff != false) {

            // Correct spillover of tiff channels specified in metadata file:
            CORRECT_SPILLOVER(ch_full_stack_dir, metadata)
            
            // Group full stack files by sample and roi_id:
            ch_full_stack_mapped_tiff = group_channel(CORRECT_SPILLOVER.out.ch_spillover_comp_tiff)

            // preprocess compensated channels with desired method:
            if (params.preprocess_method == 'cellprofiler') {
                // Preprocess channels with a specified cppipe:
                PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe, plugins)
            }
            else if (params.preprocess_method == 'hotpixel') {
                // Remove hot pixels:
                REMOVE_HOTPIXELS(CORRECT_SPILLOVER.out.ch_comp_stack_dir, metadata)
            }
            else if (params.preprocess_method == 'none') {
                // Do nothing:
                ch_full_stack_mapped_tiff = ch_full_stack_mapped_tiff
            }
            else { exit 1, "IMC channel preprocessing method not recognised!" }
            
        }

        else {

            // preprocess uncompensated channels with desired method:
            if (params.preprocess_method == 'cellprofiler') {
                // Preprocess channels with a specified cppipe:
                PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe, plugins)
            }
            else if (params.preprocess_method == 'hotpixel') {
                // Remove hot pixels:
                REMOVE_HOTPIXELS(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe, plugins)
            }
            else if (params.preprocess_method == 'none') {
                // Do nothing:
                ch_full_stack_mapped_tiff = ch_full_stack_mapped_tiff
            }
            else { exit 1, "IMC channel preprocessing method not recognised!" }
        }


        
        // Preprocess nuclear channels for nuclei specifically:
        NUCLEAR_PREPROCESS(ch_dna_stack)

        // // Segment nuclei with Unet++
        // NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)
        
        // // Dilate nuclear segmentation:
        // NUCLEAR_DILATION(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions)

        // // Join nuclear mask and segmentation stack and measure:
        // PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_dir
        //     .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
        //     .set {ch_nuc_seg_stack}

        // // Join whole cell mask and segmentation stack and measure:
        // PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_dir
        //     .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
        //     .set {ch_cell_seg_stack}

        // // Run 'simple' measurement (non-cellprofiler) of intensity + other features:
        // DILATION_MEASURE(ch_nuc_seg_stack, 'nuclei.csv')
        // CELL_MEASURE(ch_cell_seg_stack, 'cells.csv')

        // Create pseudo H&E images from nuclear + other channels:
        PSEUDO_HE(ch_dna_stack, ch_counterstain_dir)

}