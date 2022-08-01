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

include { DILATION_WF } from './workflows/primary_pipeline.nf'
include { CONSENSUS_WF; CONSENSUS_WF_ILASTIK_PP } from './workflows/CCS.nf'
include { MCD_QC } from './workflows/QC.nf'


/*
* Input
*/

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

if (params.metadata)             { ch_metadata = Channel.fromPath(params.metadata, checkIfExists: true) }                         else { exit 1, "Metadata csv file not specified!" }
if (params.full_stack_cppipe)    { ch_full_stack_cppipe = Channel.fromPath(params.full_stack_cppipe, checkIfExists: true) }       else { exit 1, "CellProfiler full stack cppipe file not specified!" }
if (params.ilastik_stack_cppipe) { ch_ilastik_stack_cppipe = Channel.fromPath(params.ilastik_stack_cppipe, checkIfExists: true) } else { exit 1, "Ilastik stack cppipe file not specified!" }
if (params.segmentation_cppipe)  { ch_segmentation_cppipe = Channel.fromPath(params.segmentation_cppipe, checkIfExists: true) }   else { exit 1, "CellProfiler segmentation cppipe file not specified!" }
if (params.nuclear_weights_directory) { ch_nuclear_weights = Channel.fromPath(params.nuclear_weights_directory, checkIfExists: true) } else { exit 1, "Nuclear weights directory not specified!" }

if (!params.skip_ilastik) {
    if (params.ilastik_training_ilp) {
        ch_ilastik_training_ilp = Channel.fromPath(params.ilastik_training_ilp, checkIfExists: true) } else { exit 1, "Ilastik training ilp file not specified!" }
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

// convert to value channels so that singular channels can be used in the pipeline multiple times without being consumed and halting the workflow:
cp_plugins = ch_cp_plugins.first()
cp_plugins.view()
compensation = ch_compensation.first()
full_stack_cppipe = ch_full_stack_cppipe.first()
ilastik_stack_cppipe = ch_ilastik_stack_cppipe.first()
segmentation_cppipe = ch_segmentation_cppipe.first()
ch_metadata = ch_metadata.first()
ch_nuclear_weights = ch_nuclear_weights.first()

workflow {

    if (params.segmentation_type == 'dilation'){
        DILATION_WF (ch_mcd, ch_metadata, ch_nuclear_weights, compensation, full_stack_cppipe, cp_plugins )
    }
    else if (params.segmentation_type == 'consensus'){
        CONSENSUS_WF (ch_mcd, ch_metadata, ch_nuclear_weights, compensation, full_stack_cppipe, segmentation_cppipe, cp_plugins )
    }
    else if (params.segmentation_type == 'consensus_il'){
        CONSENSUS_WF_ILASTIK_PP (ch_mcd, ch_metadata, ch_nuclear_weights, compensation, full_stack_cppipe, ilastik_stack_cppipe, segmentation_cppipe, cp_plugins )
    }
    else if (params.segmentation_type == 'QC'){
        MCD_QC (ch_mcd, ch_metadata)
    }
    else {
        exit 1, "Segmentation type not specified!"
    }

}



// Show help message
if (params.help) {
    helpMessage()
    exit 0
}

