/*
 * STEP 6: Output Description HTML
 */
process output_documentation {
    publishDir "${params.outdir}/deep-imcyto/${params.release}/pipeline_info", mode: params.publish_dir_mode

    input:
    path output_docs from ch_output_docs
    path images from ch_output_docs_images

    output:
    path "results_description.html"

    script:
    """
    markdown_to_html.r $output_docs results_description.html
    """
}

/*
 * Parse software version numbers
 */
process get_software_versions {
    publishDir "${params.outdir}/deep-imcyto/${params.release}/pipeline_info", mode: params.publish_dir_mode,
        saveAs: { filename ->
                      if (filename.indexOf(".csv") > 0) filename
                      else null
                }

    input:
    path imctools from ch_imctools_version.first()
    path cellprofiler from ch_cellprofiler_version.first()
    path ilastik from ch_ilastik_version.first().ifEmpty([])

    output:
    path "software_versions.csv"

    script:
    """
    echo $workflow.manifest.version > pipeline_version.txt
    echo $workflow.nextflow.version > nextflow_version.txt
    scrape_software_versions.py &> software_versions_mqc.yaml
    """
}