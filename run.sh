#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0 #Nextflow/0.32.0 #19.04.0 #Nextflow/21.04.3 #Nextflow/21.04.0 # Nextflow/20.01.0
ml Singularity/3.6.4
export NXF_SINGULARITY_CACHEDIR=/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/imcyto_nxf_singularity ## Use locally stored Singularity containers

# resultsdir = '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/results_dev_20220618_2'
# "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_TMA_REC_20190508/P1_TMA_REC_20190508.mcd"
# "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_tonsil*/*.mcd"

## RUN PIPELINE
nextflow run ./main.nf\
    --input '/camp/lab/swantonc/working/collive/rubicon/cell_segmentation/nextflow_runs/P1/20190722_Run3/mcd/*.mcd'\
    --outdir '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results'\
    --metadata './metadata.csv'\
    --full_stack_cppipe './rubicon-pipeline/assets/cppipes/full_stack_preprocessing.cppipe'\
    --segmentation_cppipe './rubicon-pipeline/assets/cppipes/segmentation_nuclei_linked.cppipe'\
    --ilastik_stack_cppipe './rubicon-pipeline/assets/cppipes/ilastik_stack_preprocessing.cppipe'\
    --compensation_tiff './rubicon-pipeline/assets/spillover/P1_imc*.tiff'\
    --plugins "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/src/rubicon-pipeline/assets/plugins"\
    --skip_ilastik true \
    --email alastair.magness@crick.ac.uk\
    --dl_conda_env "/camp/lab/swantonc/working/Alastair/.conda/envs/tf"\
    --imctools_env "/camp/lab/swantonc/working/Alastair/.conda/envs/tf"\
    --md_cuda "CUDA/10.1.105"\
    --md_conda "Anaconda3"\
    --nuclear_weights_directory "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/weights"\
    --nuclear_ppdir "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results/nuclear_preprocess"\
    --nuclear_segdir "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results/nuclear_segmentation"\
    --nuclear_dilation_radius 5\
    --profile crick
    # --resume





## "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_TMA_REC_20190508/P1_TMA_REC_20190508.mcd" \
## "/camp/lab/swantonc/inputs/flowcytometry/Katey Enfield/asb_case/Slide3_ASB/P1_Slide3_ASB_20200716_KE_HYPG/P1_Slide3_ASB_20200716_KE_HYPG.mcd"/
## "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_tonsil_start_20190508/P1_tonsil_start_20190508.mcd"
