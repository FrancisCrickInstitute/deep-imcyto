include { NUCLEAR_PREPROCESS; NUCLEAR_SEGMENTATION } from '../modules/nuclear_segmentation.nf'
include { NUCLEAR_DILATION } from '../modules/nuclear_dilation.nf'
include { IMCTOOLS; IMCTOOLS_GEN; GENERATE_METADATA } from '../modules/preprocessing.nf'
include { PREPROCESS_FULL_STACK; CELLPROFILER; PREPROCESS_MCCS_STACK; MCCS } from '../modules/cellprofiler_pp_seg.nf'
include {PSEUDO_HE } from '../modules/pseudo_HE.nf'
include {flatten_tiff ; get_roi_tuple; get_fullstack_tuple; group_channel; group_fullstack} from '../lib/core_functions.nf'


workflow CELLPROFILER {

    /*
    * The consensus cell segmentation workflow.
    */
  
    take:
        mcd
        metadata
        weights
        compensation
        cppipe_full_stack
        cppipe_consensus_cell_seg
        plugins
    
    
    main:
        // Run IMC tools on raw files:
        IMCTOOLS(mcd, metadata)

        // Group full stack files by sample and roi_id
        ch_full_stack_mapped_tiff = group_channel(IMCTOOLS.out.ch_full_stack_tiff)
        ch_dna_stack = group_channel(IMCTOOLS.out.ch_dna_stack_tiff)
        // ch_dna_stack = ch_dna_stack.flatten().collate( 4 ).view()
        // ch_dna1 = group_channel(IMCTOOLS.out.ch_dna1)
        // ch_dna2 = group_channel(IMCTOOLS.out.ch_dna2)
        ch_Ru = group_channel(IMCTOOLS.out.ch_Ru)

        PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe_full_stack, plugins)
        
        NUCLEAR_PREPROCESS(ch_dna1, ch_dna2)

        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)

        PSEUDO_HE(ch_dna1, ch_dna2, ch_Ru)

        PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_stack}

        // Run consensus cell segmentation with CCS cellprofiler pipeline:
        CELLPROFILER(ch_seg_stack, cppipe_consensus_cell_seg, plugins)
  
}

workflow MCCS {

    /*
    * The consensus cell segmentation workflow.
    */
  
    take:
        mcd
        metadata
        weights
        compensation
        cppipe_full_stack
        cppipe_mccs_stack
        cppipe_consensus_cell_seg
        plugins
    
    
    main:
        // Generate metadata if not explicitely provided:
        if (params.generate_metadata == true) {
            GENERATE_METADATA(mcd)
            imctools_input = GENERATE_METADATA.out.mcd_metadata_tuple
            imctools_input.view()
            IMCTOOLS_GEN(imctools_input)
            // Group full stack files by sample and roi_id
            ch_full_stack_mapped_tiff = group_channel(IMCTOOLS_GEN.out.ch_full_stack_tiff)
            ch_dna_stack = group_channel(IMCTOOLS_GEN.out.ch_dna_stack_tiff)
            ch_dna_stack = ch_dna_stack.flatten().collate( 4 ).view()
            ch_counterstain_dir = group_fullstack(IMCTOOLS_GEN.out.ch_counterstain_dir)
        }
        else {
            // Run IMC tools on raw files:
            IMCTOOLS(mcd, metadata)
            
            // Group full stack files by sample and roi_id
            ch_full_stack_mapped_tiff = group_channel(IMCTOOLS.out.ch_full_stack_tiff)
            ch_dna_stack = group_channel(IMCTOOLS.out.ch_dna_stack_tiff)
            ch_dna_stack = ch_dna_stack.flatten().collate( 4 ).view()
            ch_counterstain_dir = group_fullstack(IMCTOOLS.out.ch_counterstain_dir)
        }
        
        // Run Preprocessing on Full Stack, Ilastik stack and nuclear channels for unet++ segmentation:
        PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe_full_stack, plugins)
        PREPROCESS_MCCS_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe_mccs_stack, plugins)
        NUCLEAR_PREPROCESS(ch_dna_stack)

        // Make Pseudo H&E:
        PSEUDO_HE(ch_dna_stack, ch_counterstain_dir)

        // Run Nuclear Segmentation:
        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)

        // Combine outputs of PREPROCESS_FULL_STACK and PREPROCESS_MCCS_STACK, & NUCLEAR_SEGMENTATION:
        PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff
            .join(PREPROCESS_MCCS_STACK.out.ch_preprocess_mccs_stack_tiff, by: [0,1])
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_stack}

        // Run consensus cell segmentation with CCS cellprofiler pipeline:
        MCCS(ch_seg_stack, cppipe_consensus_cell_seg, plugins)

        
}