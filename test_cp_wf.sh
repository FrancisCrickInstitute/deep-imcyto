#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0
ml Singularity/3.6.4
export SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'
export NXF_SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'


## RUN PIPELINE
nextflow run ./main.nf\
    --input "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_TMA_REC_20190508/P1_TMA_REC_20190508.mcd" \
    --outdir '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results_consensus_il_test'\
    --metadata '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/src/rubicon-deep-imcyto/assets/metadata/run_1_metadata_test.csv'\
    --full_stack_cppipe './assets/cppipes/full_stack_preprocessing.cppipe'\
    --segmentation_cppipe './assets/cppipes/segmentationP1.cppipe'\
    --mccs_stack_cppipe './assets/cppipes/mccs_stack_preprocessing.cppipe'\
    --compensation_tiff "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/src/rubicon-deep-imcyto/assets/spillover/P1_imc_sm_pixel_adaptive.tiff"\
    --plugins "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/src/rubicon-deep-imcyto/assets/plugins"\
    --skip_ilastik true \
    --email alastair.magness@crick.ac.uk\
    --nuclear_weights_directory "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/weights"\
    --segmentation_type 'consensus_il'\
    -profile crick\