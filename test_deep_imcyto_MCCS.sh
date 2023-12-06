
#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0
ml Singularity/3.6.4

# Define a folder on your system for the deep-imcyto software containers to be stored (space required ~10GB):
export NXF_SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'


# RUN DEEP-IMCYTO:
nextflow run ./main.nf\
    --input "/camp/project/proj-tracerx-lung/tctProjects/rubicon/PHLEX/test_files/test_images_20230807/*.tiff"\
    --outdir '../results'\
    --release 'MCCS'\
    --metadata 'assets/metadata/PHLEX_test_metadata.csv'\
    --nuclear_weights_directory "/camp/lab/swantonc/working/Alastair/pipeline_tests/PHLEX_testing/deep-imcyto_weights"\
    --segmentation_workflow 'MCCS'\
    --full_stack_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/preinvasive/imc/outputs/PHLEX/release_20230505/MCCS/full_stack_preprocessingP1.cppipe"\
    --segmentation_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/preinvasive/imc/outputs/PHLEX/release_20230505/MCCS/segmentationP1.cppipe"\
    --mccs_stack_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/preinvasive/imc/outputs/PHLEX/release_20230505/MCCS/mccs_stack_preprocessingP1.cppipe"\
    --compensation_tiff "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/preinvasive/imc/outputs/PHLEX/release_20230505/MCCS/P1_imc_sm_pixel_adaptive.tiff"\
    --plugins "$PWD/assets/plugins"\
    --singularity_bind_path '/camp,/nemo'\
    -profile crick\
    -w '/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work'\
    # -resume