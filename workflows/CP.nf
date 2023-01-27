include { NUCLEAR_PREPROCESS; NUCLEAR_SEGMENTATION } from '../modules/nuclear_segmentation.nf'
include { NUCLEAR_DILATION } from '../modules/nuclear_dilation.nf'
include { IMCTOOLS } from '../modules/imctools.nf'
include { PREPROCESS_FULL_STACK; CONSENSUS_CELL_SEGMENTATION; PREPROCESS_MCCS_STACK; CONSENSUS_CELL_SEGMENTATION_ILASTIK_PP } from '../modules/cellprofiler_pp_seg.nf'
include {PSEUDO_HE } from '../modules/pseudo_HE.nf'
include {flatten_tiff ; get_roi_tuple ; group_channel} from '../lib/core_functions.nf'


workflow CONSENSUS_WF {

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
        ch_dna1 = group_channel(IMCTOOLS.out.ch_dna1)
        ch_dna2 = group_channel(IMCTOOLS.out.ch_dna2)
        ch_Ru = group_channel(IMCTOOLS.out.ch_Ru)

        PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe_full_stack, plugins)
        
        NUCLEAR_PREPROCESS(ch_dna1, ch_dna2)

        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)

        PSEUDO_HE(ch_dna1, ch_dna2, ch_Ru)

        PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_stack}

        // Run consensus cell segmentation with CCS cellprofiler pipeline:
        CONSENSUS_CELL_SEGMENTATION(ch_seg_stack, cppipe_consensus_cell_seg, plugins)
  
}

workflow CONSENSUS_WF_ILASTIK_PP {

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
        // Run IMC tools on raw files:
        IMCTOOLS(mcd, metadata)

        // Group full stack files by sample and roi_id
        ch_full_stack_mapped_tiff = group_channel(IMCTOOLS.out.ch_full_stack_tiff)
        ch_dna1 = group_channel(IMCTOOLS.out.ch_dna1)
        ch_dna2 = group_channel(IMCTOOLS.out.ch_dna2)
        ch_Ru = group_channel(IMCTOOLS.out.ch_Ru)


        // Run Preprocessing on Full Stack, Ilastik stack and nuclear channels for unet++ segmentation:
        PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe_full_stack, plugins)
        PREPROCESS_MCCS_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe_mccs_stack, plugins)
        NUCLEAR_PREPROCESS(ch_dna1, ch_dna2)

        // Make Pseudo H&E:
        PSEUDO_HE(ch_dna1, ch_dna2, ch_Ru)

        // Run Nuclear Segmentation:
        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)

        // Combine outputs of PREPROCESS_FULL_STACK and PREPROCESS_MCCS_STACK, & NUCLEAR_SEGMENTATION:
        PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff
            .join(PREPROCESS_MCCS_STACK.out.ch_preprocess_mccs_stack_tiff, by: [0,1])
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_stack}

        // Run consensus cell segmentation with CCS cellprofiler pipeline:
        CONSENSUS_CELL_SEGMENTATION_ILASTIK_PP(ch_seg_stack, cppipe_consensus_cell_seg, plugins)
  
}