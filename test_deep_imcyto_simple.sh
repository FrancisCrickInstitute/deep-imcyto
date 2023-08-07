
#!/bin/bash

## LOAD MODULES
ml purge
ml Nextflow/22.04.0
ml Singularity/3.6.4

# Define folder for deep-imcyto software containers to be stored:
export NXF_SINGULARITY_CACHEDIR='/camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto'


# RUN PIPELINE: test
nextflow run ./main.nf\
    --input "/camp/project/proj-tracerx-lung/tctProjects/rubicon/PHLEX/test_files/test_images_20230807/*.tiff"\
    --outdir '../results'\
    --release 'simple_segmentation'\
    --metadata 'assets/metadata/PHLEX_test_metadata.csv'\
    --nuclear_weights_directory "../deep-imcyto_weights"\
    --segmentation_workflow 'simple'\
    --nuclear_dilation_radius 1\
    --preprocess_method 'none'\
    --n_neighbours 5\
    --singularity_bind_path '/camp,/nemo'\
    -profile crick\
    -w '/camp/project/proj-tracerx-lung/txscratch/rubicon/deep_imcyto/work'\
    # -resume
