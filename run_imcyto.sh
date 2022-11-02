#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0
ml Singularity/3.6.4

# export NXF_SINGULARITY_CACHEDIR='/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/containers'
export NXF_SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'

## RUN PIPELINE
nextflow run ./main.nf\
    --input "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/test_images/20220624_ZR_HypM_TMA/20220624_ZR_HypM_TMA.mcd"\
    --outdir '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results_zr_hotpixel'\
    --metadata '/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/metadata/panel_metadata.csv'\
    --full_stack_cppipe './assets/cppipes/full_stack_preprocessing.cppipe'\
    --segmentation_cppipe './assets/cppipes/segmentationP1.cppipe'\
    --ilastik_stack_cppipe './assets/cppipes/ilastik_stack_preprocessing.cppipe'\
    --plugins "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/rubicon-deep-imcyto/assets/plugins"\
    --email alastair.magness@crick.ac.uk\
    --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
    --segmentation_type 'dilation'\
    --nuclear_dilation_radius 5\
    --preprocess_method 'hotpixel'\
    -profile crick\
    -w '/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work'\
    -resume


# ## RUN PIPELINE
# nextflow run ./main.nf\
#     --input "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/test_images/20220624_ZR_HypM_TMA/20220624_ZR_HypM_TMA.mcd"\
#     --outdir '/camp/project/proj-sahaie-swantonc/working/imc_segmentation/results/test'\
#     --metadata '/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/metadata/panel_metadata.csv'\
#     --full_stack_cppipe './assets/cppipes/full_stack_preprocessing.cppipe'\
#     --segmentation_cppipe './assets/cppipes/segmentationP1.cppipe'\
#     --ilastik_stack_cppipe './assets/cppipes/ilastik_stack_preprocessing.cppipe'\
#     --plugins "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/rubicon-deep-imcyto/assets/plugins"\
#     --email zoe.ramsden@crick.ac.uk\
#     --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
#     --segmentation_type 'dilation'\
#     --nuclear_dilation_radius 5\
#     --preprocess_method 'none'\
#     -profile crick\
#     -w '/camp/project/proj-sahaie-swantonc/working/imc_segmentation/work'\

