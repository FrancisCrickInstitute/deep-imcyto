#!/bin/bash

# To see the installed packages within the deep-imcyto container, run the following commands:
'''
singularity exec -B /camp /camp/project/proj-tracerx-lung/tctProjects/rubicon/inputs/containers/deep-imcyto/magnesa-phlex-deepimcyto_3.img /camp/project/proj-tracerx-lung/tctProjects/rubicon/PHLEX/release_testing/deep-imcyto/2023-01-25/rubicon-deep-imcyto/container_list.sh
'''

conda env list
source activate rapids

conda list -e > deep_imcyto_conda_pkg_list.txt
