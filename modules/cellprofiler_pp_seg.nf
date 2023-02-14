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


// /*
//  * STEP 4: Ilastik
//  */
// if (params.skip_ilastik) {
//     ch_preprocess_full_stack_tiff
//         .join(ch_preprocess_mccs_stack_tiff, by: [0,1])
//         .map { it -> [ it[0], it[1], [ it[2], it[3] ].flatten().sort()] }
//         .map { it -> it + [file("${params.nuclear_segdir}/p1/postprocess_predictions/${it[0]}-${it[1]}_nuclear_mask.tiff")] }
//         .set { ch_preprocess_full_stack_tiff }
//     ch_ilastik_version = Channel.empty()
// } else {
//     process ILASTIK {
//         tag "${name}.${roi}"
//         label 'process_medium'
//         publishDir "${params.outdir}/deep-imcyto/${params.release}/ilastik/${name}/${roi}", mode: params.publish_dir_mode,
//             saveAs: { filename ->
//                           if (filename.indexOf("version.txt") > 0) null
//                           else filename
//                     }

//         input:
//         tuple val(name), val(roi), path(tiff) from ch_preprocess_mccs_stack_tiff
//         path ilastik_training_ilp from ch_ilastik_training_ilp

//         output:
//         tuple val(name), val(roi), path("*.tiff"), emit: ch_ilastik_tiff
//         path "*version.txt", emit: ch_ilastik_version

//         script:
//         """
//         cp $ilastik_training_ilp ilastik_params.ilp

//         /ilastik-release/run_ilastik.sh \\
//             --headless \\
//             --project=ilastik_params.ilp \\
//             --output_format="tiff sequence" \\
//             --output_filename_format=./{nickname}_{result_type}_{slice_index}.tiff \\
//             --logfile ./ilastik_log.txt \\
//             $tiff
//         rm  ilastik_params.ilp

//         /ilastik-release/bin/python -c "import ilastik; print(ilastik.__version__)" > ilastik_version.txt
//         """
//     }

//     ch_preprocess_full_stack_tiff
//         .join(ch_ilastik_tiff, by: [0,1])
//         .map { it -> [ it[0], it[1], [ it[2], it[3] ].flatten().sort() ]}
//         .map { it -> it + [file("${params.nuclear_segdir}/p1/postprocess_predictions/${it[0]}-${it[1]}_nuclear_mask.tiff")] }
//         .set { ch_preprocess_full_stack_tiff }
// }

// ch_preprocess_full_stack_tiff.into{ ch_preprocess_full_stack_tiff_CP; ch_preprocess_full_stack_tiff_dilation}

// /*
//  * STEP 5: Segmentation with CellProfiler
//  */

process CONSENSUS_CELL_SEGMENTATION {

    tag "${name}.${roi}"
    label 'process_medium'
    publishDir "${params.outdir}/deep-imcyto/${params.release}/consensus_cell_segmentation/${name}/${roi}", mode: params.publish_dir_mode

    input:
    tuple val(name), val(roi), path(tiff), path(mask)
    path(cppipe)
    path(plugin_dir)

    output:
    path "*.{csv,tiff}"

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

process CONSENSUS_CELL_SEGMENTATION_MCCS_PP {

    tag "${name}.${roi}"
    label 'process_medium'
    publishDir "${params.outdir}/deep-imcyto/${params.release}/consensus_cell_segmentation/${name}/${roi}", mode: params.publish_dir_mode

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
