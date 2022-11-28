
#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0
ml Singularity/3.6.4

# Define folder for deep-imcyto software containers to be stored:
export NXF_SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'

# # RUN PIPELINE:
# nextflow run ./main.nf\
#     --input "/camp/path/to/data/my_image.mcd"\
#     --outdir '/camp/path/to/results'\
#     --metadata '/camp/path/to/channel_metadata_deepimcyto.csv'\
#     --nuclear_weights_directory "/camp/path/to/weights"\ # The path to the directory containing the neural network weights.
#     --segmentation_workflow 'simple'\
#     --nuclear_dilation_radius 5\
#     --preprocess_method 'hotpixel'\
#     --email username@crick.ac.uk\
#     -profile crick\
#     -w '/path/to/work/directory' # Path to a suitable directory where the nextflow will save working/interim files e.g. lab scratch directory.




# # RUN PIPELINE: sharavan
# nextflow run ./main.nf\
#     --input "/camp/lab/swantonc/inputs/yunevam/Sharavan Venkateswaran/20220513_Sharavan_WT_DESI/20220513_Sharavan_WT_DESI/20220513_Sharavan_WT_DESI.mcd"\
#     --outdir '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results_sharavan_imctools'\
#     --metadata '/camp/project/proj-tracerx-lung/tctProjects/rubicon/non_rubicon_datasets/sharavan_venkateswaran/metadata/channel_metadata_deepimcyto.csv'\
#     --email alastair.magness@crick.ac.uk\
#     --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
#     --segmentation_workflow 'simple'\
#     --nuclear_dilation_radius 5\
#     --preprocess_method 'hotpixel'\
#     --n_neighbours 5\
#     -profile crick\
#     -w '/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work'\
#     -resume

# nextflow run ./main.nf\
#     --input "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/test_images/20220624_ZR_HypM_TMA/20220624_ZR_HypM_TMA.mcd"\
#     --outdir '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/dsl2_testing/results_zoe_test'\
#     --metadata '/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/metadata/panel_metadata.csv'\
#     --email alastair.magness@crick.ac.uk\
#     --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
#     --segmentation_workflow 'simple'\
#     --nuclear_dilation_radius 5\
#     --preprocess_method 'hotpixel'\
#     -profile crick\
#     -w '/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work'\
#     -resume

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

#     --input "/camp/lab/swantonc/inputs/yunevam/Sharavan Venkateswaran/20210303_SV_HypM_azoVSveh_DESI_S2/20210303_SV_HypM_azoVSveh_DESI_S2.mcd"\
#     --input "/camp/lab/swantonc/working/Alastair/inputs/imc_other/sharavan/test/20210215_SV_HypM.mcd"\


# RUN PIPELINE: katey
nextflow run ./main.nf\
    --input "/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx421/imc/inputs/p1/tx421_20220713/mcd/*.mcd"\
    --outdir '/camp/project/proj-tracerx-lung/tctProjects/rubicon/qc/tx421/imc/outputs/PHLEX/qc_20220713/p1'\
    --metadata '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx421/imc/inputs/p1/tx421_20220713/metadata.csv'\
    --email alastair.magness@crick.ac.uk\
    --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
    --segmentation_workflow 'simple'\
    --nuclear_dilation_radius 5\
    --preprocess_method 'hotpixel'\
    --n_neighbours 5\
    -profile crick\
    -w '/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work'\
    -resume