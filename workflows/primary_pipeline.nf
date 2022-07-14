include { NUCLEAR_PREPROCESS; NUCLEAR_SEGMENTATION } from '../modules/nuclear_segmentation.nf'
include { NUCLEAR_DILATION } from '../modules/nuclear_dilation.nf'
include { IMCTOOLS } from '../modules/imctools.nf'
include { PREPROCESS_FULL_STACK } from '../modules/cellprofiler_pp_seg.nf'
include {PSEUDO_HE } from '../modules/pseudo_HE.nf'
include {flatten_tiff ; get_roi_tuple} from '../lib/core_functions.nf'

workflow DILATION_WF {

    //TO DO: THIS SPAWNS MULTIPLE SEGMENTATION RUNS, WITH EACH SEGMENTING 
    //ALL THE FILES FROM EACH MCD IN THE INPUT AS IT IS PRODUCED
  
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



        // Group full stack files by sample and roi_id
        // println "IMC TOOLS:"
        // IMCTOOLS.out.ch_full_stack_tiff.view()
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


        PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe, plugins)
        
        NUCLEAR_PREPROCESS(ch_dna1, ch_dna2)
        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)
        PSEUDO_HE(ch_dna1, ch_dna2, ch_Ru)
        
        PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_stack}

        // TO DO : CONNECT NUC SEGMENTATION OUTPUT TO NUCLEAR DILATION
        NUCLEAR_DILATION(ch_seg_stack)
  
}