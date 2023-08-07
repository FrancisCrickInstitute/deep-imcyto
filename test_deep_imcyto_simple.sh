
#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0
ml Singularity/3.6.4

# Define folder for deep-imcyto software containers to be stored:
export NXF_SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'


# RUN PIPELINE: test
nextflow run ./main.nf\
    --input "/camp/project/proj-tracerx-lung/tctProjects/rubicon/non_rubicon_datasets/van_maldegem_valand_2021/IMC_ometiff_files/*.tiff"\
    --outdir '../results'\
    --release 'simple_segmentation_1px'\
    --generate_metadata true\
    --email alastair.magness@crick.ac.uk\
    --nuclear_weights_directory "/camp/project/proj-sahaie-swantonc/working/imc_segmentation/src/weights"\
    --segmentation_workflow 'simple'\
    --nuclear_dilation_radius 1\
    --preprocess_method 'none'\
    --n_neighbours 5\
    --singularity_bind_path '/camp,/nemo'\
    -profile crick\
    -w '/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work'\
    -resume
