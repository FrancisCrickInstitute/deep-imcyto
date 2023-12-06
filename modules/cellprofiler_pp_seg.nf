/*
 * STEP 2: Preprocess full stack images with CellProfiler
 */
process PREPROCESS_FULL_STACK {

    tag "${name}.${roi}"
    label 'process_low'
    publishDir "${params.outdir}/deep-imcyto/${params.release}/channel_preprocess/${name}/${roi}", mode: params.publish_dir_mode,
        saveAs: { filename ->
                      if (filename.indexOf("version.txt") > 0) null
                      else filename
                }

    input:
    tuple val(name), val(roi), path(tiff)
    path(ctiff)
    path(cppipe)
    path(plugin_dir)

    output:
    tuple val(name), val(roi), path("full_stack/*"), emit: ch_preprocess_full_stack_tiff
    tuple val(name), val(roi), path("full_stack"), emit: ch_preprocess_full_stack_dir
    path "*version.txt", emit: ch_cellprofiler_version

    script:
    """
    export _JAVA_OPTIONS="-Xms${task.memory.toGiga()/2}g -Xmx${task.memory.toGiga()}g"
    cellprofiler \\
        --run-headless \\
        --pipeline $cppipe \\
        --image-directory . \\
        --plugins-directory $plugin_dir \\
        --output-directory ./full_stack \\
        --log-level DEBUG \\
        --temporary-directory ./tmp

    cellprofiler --version > cellprofiler_version.txt
    """
}


/*
 * STEP 3: Preprocess Ilastik stack images with CellProfiler
 */
process PREPROCESS_MCCS_STACK {
    tag "${name}.${roi}"
    label 'process_low'
    publishDir "${params.outdir}/deep-imcyto/${params.release}/channel_preprocess/${name}/${roi}", mode: params.publish_dir_mode

    input:
    tuple val(name), val(roi), path(tiff)
    path ctiff
    path cppipe
    path plugin_dir

    output:
    tuple val(name), val(roi), path("mccs_stack/*"), emit: ch_preprocess_mccs_stack_tiff

    script:
    """
    export _JAVA_OPTIONS="-Xms${task.memory.toGiga()/2}g -Xmx${task.memory.toGiga()}g"
    cellprofiler \\
        --run-headless \\
        --pipeline $cppipe \\
        --image-directory ./ \\
        --plugins-directory ./${plugin_dir} \\
        --output-directory ./mccs_stack \\
        --log-level DEBUG \\
        --temporary-directory ./tmp
    """
}


process CELLPROFILER {

    tag "${name}.${roi}"
    label 'process_medium'
    publishDir "${params.outdir}/deep-imcyto/${params.release}/CellProfiler/${name}/${roi}", mode: params.publish_dir_mode

    input:
    tuple val(name), val(roi), path(tiff), path(mask)
    path(cppipe)
    path(plugin_dir)

    output:
    path "*.{csv,tiff,png}"

    script:
    """
    echo tiff_files: ${tiff}
    echo mask_files: ${mask}
    echo cppipe: ${cppipe}
    echo plugin_dir: ${plugin_dir}

    export _JAVA_OPTIONS="-Xms${task.memory.toGiga()/2}g -Xmx${task.memory.toGiga()}g"
    cellprofiler \\
        --run-headless \\
        --pipeline $cppipe \\
        --image-directory ./ \\
        --plugins-directory ./$plugin_dir \\
        --output-directory ./ \\
        --log-level DEBUG \\
        --temporary-directory ./tmp
    """
}

process MCCS {

    tag "${name}.${roi}"
    label 'process_medium'
    publishDir "${params.outdir}/deep-imcyto/${params.release}/MCCS/${name}/${roi}", mode: params.publish_dir_mode

    input:
    tuple val(name), val(roi), path(tiff), path(pp_tiffs),path(mask)
    path(cppipe)
    path(plugin_dir)

    output:
    path "*.{csv,tiff,png}"

    script:
    """
    echo tiff_files: ${tiff}
    echo mask_files: ${mask}
    echo pp_tiffs: ${pp_tiffs}
    echo cppipe: ${cppipe}
    echo plugin_dir: ${plugin_dir}

    export _JAVA_OPTIONS="-Xms${task.memory.toGiga()/2}g -Xmx${task.memory.toGiga()}g"
    cellprofiler \\
        --run-headless \\
        --pipeline $cppipe \\
        --image-directory ./ \\
        --plugins-directory ./$plugin_dir \\
        --output-directory ./ \\
        --log-level DEBUG \\
        --temporary-directory ./tmp
    """
}
