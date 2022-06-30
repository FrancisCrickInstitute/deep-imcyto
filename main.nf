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

include { NUCLEAR_WF } from './workflows/primary_pipeline.nf'

println params.nuclear_ppdir
println params.nuclear_segdir
println params.nuclear_weights_directory

params.segmentation_type = "dilation" //"dilation" or "cellprofiler"
params.nuclear_weights_directory = './weights'


params.imctoolsdir = '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/results_dev_20220618/imctools'
params.nuclear_ppdir = "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results/nuclear_preprocess"

ch_nuclear_ppdir = Channel.value(params.nuclear_ppdir)
ch_nuclear_segdir = Channel.value(params.nuclear_segdir)
ch_nuclear_weights = Channel.value(params.nuclear_weights_directory)
ch_imctoolsdir = Channel.value(params.imctoolsdir)


parseInputs()


/*****************
* BEGIN PIPELINE *
*****************/
workflow {
  
  NUCLEAR_WF (ch_mcd, ch_metadata, ch_imctoolsdir, ch_nuclear_ppdir, ch_nuclear_segdir, ch_nuclear_weights, ch_compensation, ch_full_stack_cppipe, ch_cp_plugins )
  
}



// Show help message
if (params.help) {
    helpMessage()
    exit 0
}

