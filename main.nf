#!/usr/bin/env nextflow
/*
========================================================================================
                         nf-core/imcyto
========================================================================================
 nf-core/imcyto Analysis Pipeline.
 #### Homepage / Documentation
 https://github.com/nf-core/imcyto
----------------------------------------------------------------------------------------
*/

nextflow.enable.dsl=2

include { helpMessage; parseInputs;
           } from './lib/core_functions.nf'

include {DILATION_WF } from './workflows/primary_pipeline.nf'

println params.nuclear_ppdir
println params.nuclear_segdir
println params.nuclear_weights_directory

// params.segmentation_type = "dilation" //"dilation" or "cellprofiler"
// params.nuclear_weights_directory = './weights'




// {custom_runName; ch_output_docs; ch_output_docs_images; ch_mcd; ch_metadata; ch_full_stack_cppipe; ch_ilastik_stack_cppipe; ch_segmentation_cppipe; ch_ilastik_training_ilp; ch_compensation; ch_cp_plugins} = parseInputs()
// parseInputs(params)

/*
* Input
*/

/*
* Make channels for nuclear segmentation
*/

ch_nuclear_ppdir = Channel.value(params.nuclear_ppdir)
ch_nuclear_segdir = Channel.value(params.nuclear_segdir)
ch_nuclear_weights = Channel.value(params.nuclear_weights_directory)
ch_imctoolsdir = Channel.value(params.imctoolsdir)

// Has the run name been specified by the user?
// this has the bonus effect of catching both -name and --name
custom_runName = params.name
if (!(workflow.runName ==~ /[a-z]+_[a-z]+/)) {
    custom_runName = workflow.runName
}

// Stage config files
ch_output_docs = file("$baseDir/docs/output.md", checkIfExists: true)
ch_output_docs_images = file("$baseDir/docs/images/", checkIfExists: true)

/*
* Validate inputs
*/
if (params.input) {
    Channel
        .fromPath(params.input, checkIfExists: true)
        .map { it -> [ it.name.take(it.name.lastIndexOf('.')), it ] }
        .ifEmpty { exit 1, "Input file not found: ${params.input}" }
        .set { ch_mcd }
} else {
exit 1, "Input file not specified!"
}

if (params.metadata)             { ch_metadata = file(params.metadata, checkIfExists: true) }                         else { exit 1, "Metadata csv file not specified!" }
if (params.full_stack_cppipe)    { ch_full_stack_cppipe = file(params.full_stack_cppipe, checkIfExists: true) }       else { exit 1, "CellProfiler full stack cppipe file not specified!" }
if (params.ilastik_stack_cppipe) { ch_ilastik_stack_cppipe = file(params.ilastik_stack_cppipe, checkIfExists: true) } else { exit 1, "Ilastik stack cppipe file not specified!" }
if (params.segmentation_cppipe)  { ch_segmentation_cppipe = file(params.segmentation_cppipe, checkIfExists: true) }   else { exit 1, "CellProfiler segmentation cppipe file not specified!" }

if (!params.skip_ilastik) {
    if (params.ilastik_training_ilp) {
        ch_ilastik_training_ilp = file(params.ilastik_training_ilp, checkIfExists: true) } else { exit 1, "Ilastik training ilp file not specified!" }
}

if (params.compensation_tiff) {
    Channel
        .fromPath(params.compensation_tiff, checkIfExists: true)
        .set { ch_compensation }
} else {
    Channel
        .empty()
        .set { ch_compensation }
}

// Plugins required for CellProfiler
Channel
    .fromPath(params.plugins, type: 'dir' , checkIfExists: true)
    .set { ch_cp_plugins }

/*****************
* BEGIN PIPELINE *
*****************/
workflow {
  
  DILATION_WF (ch_mcd, ch_metadata, ch_imctoolsdir, ch_nuclear_ppdir, ch_nuclear_segdir, ch_nuclear_weights, ch_compensation, ch_full_stack_cppipe, ch_cp_plugins )
  
}



// Show help message
if (params.help) {
    helpMessage()
    exit 0
}

