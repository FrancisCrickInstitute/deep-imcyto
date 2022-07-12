include { NUCLEAR_PREPROCESS; NUCLEAR_SEGMENTATION } from '../modules/nuclear_segmentation.nf'
include { NUCLEAR_DILATION } from '../modules/nuclear_dilation.nf'
include { IMCTOOLS } from '../modules/imctools.nf'
include { PREPROCESS_FULL_STACK; CONSENSUS_CELL_SEGMENTATION; PREPROCESS_ILASTIK_STACK; CONSENSUS_CELL_SEGMENTATION_ILASTIK_PP } from '../modules/cellprofiler_pp_seg.nf'
include {PSEUDO_HE } from '../modules/pseudo_HE.nf'
include {flatten_tiff ; get_roi_tuple } from '../lib/core_functions.nf'

// // Function to get list of [sample_id,roi_id,path_to_file]
// def flatten_tiff(ArrayList channel) {
//     def sample = channel[0]
//     def file_list = channel[1]
//     // println file_list
//     // println file_list.size()
//     def new_array = []

//     for (int i=0; i<file_list.size(); i++) {
//         def item = []
//         item.add(sample)
//         item.add(file_list[i].getParent().getParent().getName())
//         item.add(file_list[i])
//         new_array.add(item)
//     }
//     return new_array
// }

// def get_roi_tuple(ArrayList channel) {
//     //gets [sample_id,roi_id,path_to_file] for single channels, allowing for mcd with single ROIs 
//     def sample = channel[0]
//     def file_list = channel[1]
//     // println file_list.getClass()
//     // println file_list
//     if (file_list.getClass() == java.util.ArrayList) {
//         // println 'operating on arraylist'
//         def new_array = []
//         for (int i=0; i<file_list.size(); i++) {
//             def item = []
//             item.add(sample)
//             roi = file_list[i].getParent().getParent().getName()
//             // println 'ROI', roi
//             item.add(file_list[i].getParent().getParent().getName())
//             item.add(file_list[i])
//             new_array.add(item)
//             // println 'item'
//             // println item
//             // println new_array
//         }

//         return new_array
//     }
//     else {
//         def new_array = []
//         new_array.add(sample)
//         new_array.add(file_list.getParent().getParent().getName())
//         new_array.add(file_list)
//         println new_array
//         return new_array
//     }
    
// }

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
    
    // Run IMC tools on raw files:
    main:
    IMCTOOLS(mcd, metadata)

    // Group full stack files by sample and roi_id
    IMCTOOLS.out.ch_full_stack_tiff
        .map { flatten_tiff(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        // .take(-1) //.last() produced expected out[ut for roi-1]
        .set { ch_full_stack_mapped_tiff }
    
    // Group ch_dna1 files by sample and roi_id
    IMCTOOLS.out.ch_dna1
        .map { get_roi_tuple(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        .set { ch_dna1 }

    // Group ch_dna2 files by sample and roi_id
    IMCTOOLS.out.ch_dna2
        .map { get_roi_tuple(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        .set { ch_dna2 }

    // Group ch_Ru files by sample and roi_id
    IMCTOOLS.out.ch_Ru
        .map { get_roi_tuple(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        .set { ch_Ru }


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
    cppipe_ilastik_stack
    cppipe_consensus_cell_seg
    plugins
    
    // Run IMC tools on raw files:
    main:
    IMCTOOLS(mcd, metadata)

    // Group full stack files by sample and roi_id
    IMCTOOLS.out.ch_full_stack_tiff
        .map { flatten_tiff(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        // .take(-1) //.last() produced expected out[ut for roi-1]
        .set { ch_full_stack_mapped_tiff }
    
    // Group ch_dna1 files by sample and roi_id
    IMCTOOLS.out.ch_dna1
        .map { get_roi_tuple(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        .set { ch_dna1 }

    // Group ch_dna2 files by sample and roi_id
    IMCTOOLS.out.ch_dna2
        .map { get_roi_tuple(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        .set { ch_dna2 }

    // Group ch_Ru files by sample and roi_id
    IMCTOOLS.out.ch_Ru
        .map { get_roi_tuple(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        .set { ch_Ru }

    // Run Preprocessing:
    PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe_full_stack, plugins)

    PREPROCESS_ILASTIK_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe_ilastik_stack, plugins)
    
    NUCLEAR_PREPROCESS(ch_dna1, ch_dna2)

    // Make Pseudo H&E:
    PSEUDO_HE(ch_dna1, ch_dna2, ch_Ru)

    // Run Nuclear Segmentation:
    NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)

    // Combine outputs of PREPROCESS_FULL_STACK and PREPROCESS_ILASTIK_STACK, & NUCLEAR_SEGMENTATION:
    PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff
        .join(PREPROCESS_ILASTIK_STACK.out.ch_preprocess_ilastik_stack_tiff, by: [0,1])
        .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
        .set {ch_seg_stack}

    // Run consensus cell segmentation with CCS cellprofiler pipeline:
    CONSENSUS_CELL_SEGMENTATION_ILASTIK_PP(ch_seg_stack, cppipe_consensus_cell_seg, plugins)
  
}