#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0 #Nextflow/0.32.0 #19.04.0 #Nextflow/21.04.3 #Nextflow/21.04.0 # Nextflow/20.01.0
ml Singularity/3.6.4
# ml Singularity/2.6.0-foss-2016b
export SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'
export NXF_SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'

flowcytometry="/camp/stp/flowcytometry/data/labs/swantonc/outputs/Katey Enfield/InstrumentComparisons"
# "${flowcytometry}/*/*/*After*.mcd"

image="*.txt"
## RUN PIPELINE
nextflow run ./main.nf\
    --input "/camp/project/proj-tracerx-lung/tctProjects/rubicon/qc/general/imc/qc_gaschange/inputs/txt/$image"\
    --outdir '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results_txt_test'\
    --metadata '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/metadata/metadata.csv'\
    --spillover_metadata '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/src/rubicon-deep-imcyto/assets/metadata/run_1_metadata_test.csv'\
    --full_stack_cppipe './assets/cppipes/full_stack_preprocessing.cppipe'\
    --segmentation_cppipe './assets/cppipes/segmentationP1.cppipe'\
    --ilastik_stack_cppipe './assets/cppipes/ilastik_stack_preprocessing.cppipe'\
    --compensation_tiff "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/src/rubicon-deep-imcyto/assets/spillover/P2_imc_sm_pixel_adaptive.tiff"\
    --plugins "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/src/rubicon-deep-imcyto/assets/plugins"\
    --skip_ilastik true \
    --email alastair.magness@crick.ac.uk\
    --dl_conda_env "/camp/lab/swantonc/working/Alastair/.conda/envs/tf"\
    --imctools_env "/camp/lab/swantonc/working/Alastair/.conda/envs/tf"\
    --md_cuda "CUDA/10.2.89-GCC-8.3.0"\
    --md_conda "Anaconda3"\
    --nuclear_weights_directory "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/weights"\
    --segmentation_type 'QC'\
    --nuclear_dilation_radius 5\
    --preprocess_method 'hotpixel'\
    -profile crick\
    # -resume




## './assets/cppipes/segmentation_nuclei_linked.cppipe'

## "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_TMA_REC_20190508/P1_TMA_REC_20190508.mcd" \
# "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA004/*/*.mcd"
## "/camp/lab/swantonc/inputs/flowcytometry/Katey Enfield/asb_case/Slide3_ASB/P1_Slide3_ASB_20200716_KE_HYPG/P1_Slide3_ASB_20200716_KE_HYPG.mcd"/
## "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_tonsil_start_20190508/P1_tonsil_start_20190508.mcd"
# '/camp/lab/swantonc/working/collive/rubicon/cell_segmentation/nextflow_runs/P1/20190722_Run3/mcd/*.mcd'
# "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_tonsil_start_20190508/P1_tonsil_start_20190508.mcd"
# export NXF_SINGULARITY_CACHEDIR="/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/imcyto_nxf_singularity/" ## Use locally stored Singularity containers
# export NXF_SINGULARITY_LIBRARYDIR=/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/imcyto_nxf_singularity/
# resultsdir = '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/results_dev_20220618_2'
# "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_TMA_REC_20190508/P1_TMA_REC_20190508.mcd"
# "/camp/lab/swantonc/inputs/flowcytometry/Tx100/TMA_REC/P1_tonsil*/*.mcd"
# './assets/cppipes/segmentationP1_CCS_median.cppipe'

# When  we run this on all tx100 data with two metadata csvs, just run this command twice, specifying the two metadata csvs  with different filenames.
# todo: genericise base config and add specific config for rubicon.; delete m_summary.py and m_summary.pyc; remove truth.py and truth.pyc
# "consensus_il"