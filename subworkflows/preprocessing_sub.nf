include { NUCLEAR_PREPROCESS; NUCLEAR_SEGMENTATION } from '../modules/nuclear_segmentation.nf'
include { NUCLEAR_DILATION; OVERLAYS; DILATION_MEASURE; DILATION_MEASURE as CELL_MEASURE } from '../modules/nuclear_dilation.nf'
include { PREPROCESS_FULL_STACK } from '../modules/cellprofiler_pp_seg.nf'
include {PSEUDO_HE } from '../modules/pseudo_HE.nf'
include {flatten_tiff ; get_roi_tuple; get_fullstack_tuple; group_channel; group_fullstack} from '../lib/core_functions.nf'
include {IMCTOOLS; CORRECT_SPILLOVER; REMOVE_HOTPIXELS} from '../modules/preprocessing.nf'



workflow NoCompNoPreprocess {

    take:
        ch_full_stack_dir
        ch_dna_stack
        ch_counterstain_dir
        weights

    main:

        // Do nothing:
        ch_full_stack_dir = ch_full_stack_dir

        // Preprocess nuclear channels for nuclei specifically:
        NUCLEAR_PREPROCESS(ch_dna_stack)

        // Segment nuclei with Unet++
        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)
        
        // Dilate nuclear segmentation:
        NUCLEAR_DILATION(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions)

        // Join nuclear mask and segmentation stack and measure:
        ch_full_stack_dir
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_nuc_seg_stack}

        // Join whole cell mask and segmentation stack and measure:
        ch_full_stack_dir
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_cell_seg_stack}

        // Run 'simple' measurement (non-cellprofiler) of intensity + other features:
        DILATION_MEASURE(ch_nuc_seg_stack, 'nuclei.csv')
        CELL_MEASURE(ch_cell_seg_stack, 'cells.csv')

        // Create pseudo H&E images from nuclear + other channels:
        PSEUDO_HE(ch_dna_stack, ch_counterstain_dir)

        // Join masks and nuc ikmages for segmentation overlay images:
        NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_overlay}

        ch_seg_overlay
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_seg_overlay}

        OVERLAYS(ch_seg_overlay)

}

workflow NoCompHotPixel {


    take:
        ch_full_stack_dir
        ch_dna_stack
        ch_counterstain_dir
        weights
        metadata

    main:
        
        // Remove hot pixels:
        REMOVE_HOTPIXELS(ch_full_stack_dir, metadata)
        
        // Preprocess nuclear channels for nuclei specifically:
        NUCLEAR_PREPROCESS(ch_dna_stack)

        // Segment nuclei with Unet++
        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)
        
        // Dilate nuclear segmentation:
        NUCLEAR_DILATION(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions)

        // Join nuclear mask and segmentation stack and measure:
        REMOVE_HOTPIXELS.out.ch_hp_dir
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_nuc_seg_stack}

        // Join whole cell mask and segmentation stack and measure:
        REMOVE_HOTPIXELS.out.ch_hp_dir
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_cell_seg_stack}

        // Run 'simple' measurement (non-cellprofiler) of intensity + other features:
        DILATION_MEASURE(ch_nuc_seg_stack, 'nuclei.csv')
        CELL_MEASURE(ch_cell_seg_stack, 'cells.csv')

        // Create pseudo H&E images from nuclear + other channels:
        PSEUDO_HE(ch_dna_stack, ch_counterstain_dir)

        // Join masks and nuc ikmages for segmentation overlay images:
        NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_overlay}

        ch_seg_overlay
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_seg_overlay}

        OVERLAYS(ch_seg_overlay)

}

workflow NoCompCP {

    take:
        ch_full_stack_mapped_tiff
        compensation
        cppipe
        plugins

    main:
            // Preprocess channels with a specified cppipe:
        PREPROCESS_FULL_STACK(ch_full_stack_mapped_tiff, compensation.collect().ifEmpty([]), cppipe, plugins)
        
        // Join nuclear mask and segmentation stack and measure:
        PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_dir
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_nuc_seg_stack}

        // Join whole cell mask and segmentation stack and measure:
        PREPROCESS_FULL_STACK.out.ch_preprocess_full_stack_dir
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_cell_seg_stack}
}

workflow CompHotPixel {

    take:
        ch_full_stack_dir
        ch_dna_stack
        ch_counterstain_dir
        weights
        metadata

    main:

        // Correct spillover of tiff channels specified in metadata file:
        CORRECT_SPILLOVER(ch_full_stack_dir, metadata)

        // Remove hot pixels:
        REMOVE_HOTPIXELS(CORRECT_SPILLOVER.out.ch_comp_stack_dir, metadata)

        // Preprocess nuclear channels for nuclei specifically:
        NUCLEAR_PREPROCESS(ch_dna_stack)

        // Segment nuclei with Unet++
        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)
        
        // Dilate nuclear segmentation:
        NUCLEAR_DILATION(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions)

        // Join nuclear mask and segmentation stack and measure:
        REMOVE_HOTPIXELS.out.ch_hp_dir
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_nuc_seg_stack}

        // Join whole cell mask and segmentation stack and measure:
        REMOVE_HOTPIXELS.out.ch_hp_dir
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_cell_seg_stack}

        // Run 'simple' measurement (non-cellprofiler) of intensity + other features:
        DILATION_MEASURE(ch_nuc_seg_stack, 'nuclei.csv')
        CELL_MEASURE(ch_cell_seg_stack, 'cells.csv')

        // Create pseudo H&E images from nuclear + other channels:
        PSEUDO_HE(ch_dna_stack, ch_counterstain_dir)

         // Join masks and nuc ikmages for segmentation overlay images:
        NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_overlay}

        ch_seg_overlay
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_seg_overlay}

        OVERLAYS(ch_seg_overlay)

}

workflow CompNoPreprocess {

    take:
        ch_full_stack_dir
        ch_dna_stack
        ch_counterstain_dir
        weights
        metadata

    main:

        // Correct spillover of tiff channels specified in metadata file:
        CORRECT_SPILLOVER(ch_full_stack_dir, metadata)

        ch_comp_stack_dir = CORRECT_SPILLOVER.out.ch_comp_stack_dir

        // Preprocess nuclear channels for nuclei specifically:
        NUCLEAR_PREPROCESS(ch_dna_stack)

        // Segment nuclei with Unet++
        NUCLEAR_SEGMENTATION(NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei, weights)
        
        // Dilate nuclear segmentation:
        NUCLEAR_DILATION(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions)

        // Join nuclear mask and segmentation stack and measure:
        ch_comp_stack_dir
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_nuc_seg_stack}

        // Join whole cell mask and segmentation stack and measure:
        ch_comp_stack_dir
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_cell_seg_stack}

        // Run 'simple' measurement (non-cellprofiler) of intensity + other features:
        DILATION_MEASURE(ch_nuc_seg_stack, 'nuclei.csv')
        CELL_MEASURE(ch_cell_seg_stack, 'cells.csv')

        // Create pseudo H&E images from nuclear + other channels:
        PSEUDO_HE(ch_dna_stack, ch_counterstain_dir)

         // Join masks and nuc ikmages for segmentation overlay images:
        NUCLEAR_PREPROCESS.out.ch_preprocessed_nuclei
            .join(NUCLEAR_SEGMENTATION.out.ch_nuclear_predictions, by: [0,1])
            .set {ch_seg_overlay}

        ch_seg_overlay
            .join(NUCLEAR_DILATION.out.ch_nuclear_dilation, by: [0,1])
            .set {ch_seg_overlay}

        OVERLAYS(ch_seg_overlay)
}
