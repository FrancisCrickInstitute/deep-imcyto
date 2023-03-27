#!/bin/bash
#SBATCH --partition=cpu
#SBATCH --ntasks 1
#SBATCH --mem 32GB
#SBATCH --time 24:00:0
#SBATCH --job-name p2_peace_20201217
#SBATCH --mail-type=begin
#SBATCH --mail-type=end
#SBATCH --mail-user=alastair.magness@crick.ac.uk

#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0
ml Singularity/3.6.4

# Define folder for deep-imcyto software containers to be stored:
export NXF_SINGULARITY_CACHEDIR="/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto"

cohort="tx421"
panel="p2"
stainbatch="peace_20201217a"

# RUN DEEP-IMCYTO in MCCS mode:
nextflow run ./main.nf\
    --input "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/inputs/$panel/$stainbatch/*.mcd"\
    --outdir "../results"\
    --release "$panel/$stainbatch"\
    --email alastair.magness@crick.ac.uk\
    --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
    --segmentation_workflow "MCCS"\
    --full_stack_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/full_stack_preprocessingP2.cppipe"\
    --segmentation_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/segmentationP2.cppipe"\
    --mccs_stack_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/mccs_stack_preprocessingP2.cppipe"\
    --compensation_tiff "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/p2_peace_20211118_sm_adaptive.tiff"\
    --generate_metadata true\
    --plugins "$PWD/assets/plugins"\
    -profile crick\
    -w "/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work"\
    -resume


panel="p2"
stainbatch="peace_20201217b"

# RUN DEEP-IMCYTO in MCCS mode:
nextflow run ./main.nf\
    --input "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/inputs/$panel/$stainbatch/*.mcd"\
    --outdir "../results"\
    --release "$panel/$stainbatch"\
    --email alastair.magness@crick.ac.uk\
    --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
    --segmentation_workflow "MCCS"\
    --full_stack_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/full_stack_preprocessingP2.cppipe"\
    --segmentation_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/segmentationP2.cppipe"\
    --mccs_stack_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/mccs_stack_preprocessingP2.cppipe"\
    --compensation_tiff "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/p2_peace_20211118_sm_adaptive.tiff"\
    --generate_metadata true\
    --plugins "$PWD/assets/plugins"\
    -profile crick\
    -w "/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work"\
    -resume

cohort="tx421"
panel="p2"
stainbatch="tx421_20220713"

# RUN DEEP-IMCYTO in MCCS mode:
nextflow run ./main.nf\
    --input "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/inputs/$panel/$stainbatch/mcd/*.mcd"\
    --outdir "../results"\
    --release "$panel/$stainbatch"\
    --email alastair.magness@crick.ac.uk\
    --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
    --segmentation_workflow "MCCS"\
    --full_stack_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/full_stack_preprocessingP2.cppipe"\
    --segmentation_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/segmentationP2.cppipe"\
    --mccs_stack_cppipe "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/mccs_stack_preprocessingP2.cppipe"\
    --compensation_tiff "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/$cohort/imc/outputs/PHLEX/release_20230227/MCCS/p2_peace_20211118_sm_adaptive.tiff"\
    --generate_metadata true\
    --plugins "$PWD/assets/plugins"\
    -profile crick\
    -w "/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work"\
    -resume