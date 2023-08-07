FROM rapidsai/rapidsai:22.02-cuda11.0-base-ubuntu18.04-py3.8
# rapidsai/rapidsai:22.02-cuda11.0-base-ubuntu18.04-py3.8
# rapidsai/rapidsai:cuda11.4-base-ubuntu20.04-py3.8

ARG CONDA_PREFIX="rapids"

COPY ./pip_requirements.txt /tmp/pip_requirements.txt

# RUN source activate rapids && \
#     conda update conda && \
#     conda install -c conda-forge cudatoolkit=11.2 cudnn=8.1.0

RUN source activate rapids \
  && env \
  && conda info \
  && conda config --show-sources \
  && conda list --show-channel-urls

RUN gpuci_mamba_retry install -y -n rapids \
  "cudatoolkit cudnn"

ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:${CONDA_PREFIX}/lib:/opt/conda/envs/rapids/lib"

# # RUN mkdir -p ${CONDA_PREFIX}/etc/conda/activate.d && \
# #     echo 'ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${CONDA_PREFIX}/lib/' > ${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh

RUN source activate rapids && \
    pip install --upgrade pip && \
    pip install -r /tmp/pip_requirements.txt
    # conda env update -n rapids --file /tmp/pip_requirements.txt

RUN source activate rapids \
  && env \
  && conda info \
  && conda config --show-sources \
  && conda list --show-channel-urls

# Add conda installation dir to PATH (instead of doing 'conda activate')
# ENV PATH=/opt/conda/envs/rapids/bin:$PATH
# try setting path in the same way as rapids container:
ENV PATH="/opt/conda/condabin:/opt/conda/envs/rapids/bin:/opt/conda/bin:/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"


# Dump the details of the installed packages to a file for posterity
RUN conda env export --name rapids > rapids_container.yml

ENTRYPOINT [ "/opt/conda/bin/tini", "--", "/opt/docker/bin/entrypoint" ]

CMD [ "/bin/bash" ]
