def helpMessage() {
    log.info nfcoreHeader()
    log.info"""

    Usage:

    The typical command for running the pipeline is as follows:
      nextflow run nf-core/imcyto \
          --input "./inputs/*.mcd" \
          --metadata './inputs/metadata.csv' \
          --full_stack_cppipe './plugins/full_stack_preprocessing.cppipe' \
          --ilastik_stack_cppipe './plugins/ilastik_stack_preprocessing.cppipe' \
          --segmentation_cppipe './plugins/segmentation.cppipe' \
          --ilastik_training_ilp './plugins/ilastik_training_params.ilp' \
          --plugins './plugins/cp_plugins/' \
          -profile docker

    Mandatory arguments:
      --input [file]                  Path to input data file(s) (globs must be surrounded with quotes). Currently supported formats are *.mcd, *.ome.tiff, *.txt
      --metadata [file]               Path to metadata csv file indicating which images to merge in full stack and/or Ilastik stack
      --full_stack_cppipe [file]      CellProfiler pipeline file required to create full stack (cppipe format)
      --ilastik_stack_cppipe [file]   CellProfiler pipeline file required to create Ilastik stack (cppipe format)
      --segmentation_cppipe [file]    CellProfiler pipeline file required for segmentation (cppipe format)
      -profile [str]                  Configuration profile to use. Can use multiple (comma separated)
                                      Available: docker, singularity, awsbatch, test and more.

    Other options:
      --ilastik_training_ilp [file]   Parameter file required by Ilastik (ilp format)
      --compensation_tiff [file]      Tiff file for compensation analysis during CellProfiler preprocessing steps
      --skip_ilastik [bool]           Skip Ilastik processing step
      --plugins [file]                Path to directory with plugin files required for CellProfiler. Default: assets/plugins
      --outdir [file]                 The output directory where the results will be saved
      --publish_dir_mode [str]        Mode for publishing results in the output directory. Available: symlink, rellink, link, copy, copyNoFollow, move (Default: copy)
      --email [email]                 Set this parameter to your e-mail address to get a summary e-mail with details of the run sent to you when the workflow exits
      --email_on_fail [email]         Same as --email, except only send mail if the workflow is not successful
      -name [str]                     Name for the pipeline run. If not specified, Nextflow will automatically generate a random mnemonic.

    AWSBatch options:
      --awsqueue [str]                The AWSBatch JobQueue that needs to be set when running on AWSBatch
      --awsregion [str]               The AWS Region for your AWS Batch job to run on
      --awscli [str]                  Path to the AWS CLI tool
    """.stripIndent()
}

def nfcoreHeader() {
    // Log colors ANSI codes
    c_black = params.monochrome_logs ? '' : "\033[0;30m";
    c_blue = params.monochrome_logs ? '' : "\033[0;34m";
    c_cyan = params.monochrome_logs ? '' : "\033[0;36m";
    c_dim = params.monochrome_logs ? '' : "\033[2m";
    c_green = params.monochrome_logs ? '' : "\033[0;32m";
    c_purple = params.monochrome_logs ? '' : "\033[0;35m";
    c_reset = params.monochrome_logs ? '' : "\033[0m";
    c_white = params.monochrome_logs ? '' : "\033[0;37m";
    c_yellow = params.monochrome_logs ? '' : "\033[0;33m";

    return """    -${c_dim}--------------------------------------------------${c_reset}-
                                            ${c_green},--.${c_black}/${c_green},-.${c_reset}
    ${c_blue}        ___     __   __   __   ___     ${c_green}/,-._.--~\'${c_reset}
    ${c_blue}  |\\ | |__  __ /  ` /  \\ |__) |__         ${c_yellow}}  {${c_reset}
    ${c_blue}  | \\| |       \\__, \\__/ |  \\ |___     ${c_green}\\`-._,-`-,${c_reset}
                                            ${c_green}`._,._,\'${c_reset}
    ${c_purple}  nf-core/imcyto v${workflow.manifest.version}${c_reset}
    -${c_dim}--------------------------------------------------${c_reset}-
    """.stripIndent()
}

def checkHostname() {
    def c_reset = params.monochrome_logs ? '' : "\033[0m"
    def c_white = params.monochrome_logs ? '' : "\033[0;37m"
    def c_red = params.monochrome_logs ? '' : "\033[1;91m"
    def c_yellow_bold = params.monochrome_logs ? '' : "\033[1;93m"
    if (params.hostnames) {
        def hostname = "hostname".execute().text.trim()
        params.hostnames.each { prof, hnames ->
            hnames.each { hname ->
                if (hostname.contains(hname) && !workflow.profile.contains(prof)) {
                    log.error "====================================================\n" +
                            "  ${c_red}WARNING!${c_reset} You are running with `-profile $workflow.profile`\n" +
                            "  but your machine hostname is ${c_white}'$hostname'${c_reset}\n" +
                            "  ${c_yellow_bold}It's highly recommended that you use `-profile $prof${c_reset}`\n" +
                            "============================================================"
                }
            }
        }
    }
}