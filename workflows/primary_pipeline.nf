include { NUCLEAR_PREPROCESS; NUCLEAR_SEGMENTATION } from '../modules/nuclear_segmentation.nf'
include { NUCLEAR_DILATION } from '../modules/nuclear_dilation.nf'
include { IMCTOOLS } from '../modules/imctools.nf'
include { PREPROCESS_FULL_STACK } from '../modules/cellprofiler_pp_seg.nf'
include {PSEUDO_HE } from '../modules/pseudo_HE.nf'

// Function to get list of [sample_id,roi_id,path_to_file]
def flatten_tiff(ArrayList channel) {
    def sample = channel[0]
    def file_list = channel[1]
    // println file_list
    // println file_list.size()
    def new_array = []
    for (int i=0; i<file_list.size(); i++) {
        def item = []
        item.add(sample)
        item.add(file_list[i].getParent().getParent().getName())
        item.add(file_list[i])
        new_array.add(item)
    }
    return new_array
}

def get_roi_tuple(ArrayList channel) {
    def sample = channel[0]
    def file_list = channel[1]
    println file_list.getClass()
    if (file_list.getClass() == java.util.ArrayList) {
        def new_array = []
        for (int i=0; i<file_list.size(); i++) {
            def item = []
            item.add(sample)
            item.add(file_list[i].getParent().getParent().getName())
            item.add(file_list[i])
            new_array.add(item)
        return new_array
    }

    }
    else {
        def new_array = []
        new_array.add(sample)
        new_array.add(file_list.getParent().getParent().getName())
        new_array.add(file_list)
        println new_array
        return new_array
        }
    
}

workflow NUCLEAR_WF {

    //TO DO: THIS SPAWNS MULTIPLE SEGMENTATION RUNS, WITH EACH SEGMENTING 
    //ALL THE FILES FROM EACH MCD IN THE INPUT AS IT IS PRODUCED
  
    take:
    mcd
    metadata
    imctoolsdir
    nuclear_ppdir
    segdir
    weights
    compensation
    cppipe
    plugins
    
    // NUCLEAR_PREPROCESS(ch_imctoolsdir, ch_nuclear_ppdir)
    main:
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
        .set { ch_full_stack_tiff }
    // ch_full_stack_tiff.view()
    // // Group ilastik stack files by sample and roi_id
    // ch_ilastik_stack_tiff
    //     .map { flatten_tiff(it) }
    //     .flatten()
    //     .collate(3)
    //     .groupTuple(by: [0,1])
    //     .map { it -> [ it[0], it[1], it[2].sort() ] }
    //     .set { ch_ilastik_stack_tiff }

    // Group ch_dna1 files by sample and roi_id
    println "DNA 1:"
    IMCTOOLS.out.ch_dna1.view()
    a = mcd.count().view()
    println 'mcd count'
    println a
    IMCTOOLS.out.ch_dna1
        .map { get_roi_tuple(it) }
        .flatten()
        .collate(3)
        .groupTuple(by: [0,1])
        .map { it -> [ it[0], it[1], it[2].sort() ] }
        .set { ch_dna1 }
    ch_dna1.view()

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

    // ch_full_stack_tiff.into { ch_full_stack_tiff; ch_full_stack_phe }

    PREPROCESS_FULL_STACK(ch_full_stack_tiff, compensation.collect().ifEmpty([]), cppipe, plugins)
    NUCLEAR_PREPROCESS(IMCTOOLS.out.ch_imctoolsdir, nuclear_ppdir)
    NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocess_results, weights)
    PSEUDO_HE(ch_dna1, ch_dna2, ch_Ru)


    // PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff
    //     .join(PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff, by: [0,1])
    //     .map { it -> [ it[0], it[1], [ it[2], it[3] ].flatten().sort()] }
    //     .map { it -> it + [file("${segdir.val}/p1/postprocess_predictions/${it[0]}-${it[1]}_nuclear_mask.tiff")] }
    //     .set { ch_full_stack_w_preds }

    PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff
        .map { it -> [ it[0], it[1], [ it[2] ].flatten().sort()] }
        .map { it -> it + [file("${segdir.val}/p1/postprocess_predictions/${it[0]}-${it[1]}_nuclear_mask.tiff")] }
        .set { ch_full_stack_w_preds }

    // .join(PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_tiff, by: [0,1])


    NUCLEAR_DILATION(NUCLEAR_SEGMENTATION.out.ch_proceed_dilation, ch_full_stack_w_preds)
  
}