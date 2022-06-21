#!/usr/bin/env nextflow
/*
========================================================================================
                         nf-core/imcyto
========================================================================================
 nf-core/imcyto Analysis Pipeline.
 #### Homepage / Documentation
 https://github.com/nf-core/imcyto
----------------------------------------------------------------------------------------
*/

nextflow.enable.dsl=2

include { helpMessage;
           } from './lib/core_functions.nf'

include { NUCLEAR_PREPROCESS;
          NUCLEAR_SEGMENTATION } from './modules/nuclear_segmentation.nf'


println params.nuclear_ppdir
println params.nuclear_segdir
println params.nuclear_weights_directory

params.segmentation_type = "dilation" //"dilation" or "cellprofiler"
params.nuclear_weights_directory = './weights'


params.imctoolsdir = '/camp/project/proj-tracerx-lung/tctProjects/rubicon/tracerx/tx100/imc/outputs/deep_imcyto/results/imctools'

workflow Primary {
  
    ch_nuclear_ppdir = Channel.value(params.nuclear_ppdir)
    ch_nuclear_segdir = Channel.value(params.nuclear_segdir)
    ch_nuclear_weights = Channel.value(params.nuclear_weights_directory)
    ch_imctoolsdir = Channel.value(params.imctools_dir)
    
    NUCLEAR_PREPROCESS(ch_imctoolsdir, ch_nuclear_ppdir)
    // ch_nhood | NEIGHBOURHOOD_GRAPH() | GRAPH_BARRIER() 
  
}

// ch_nuclear_ppdir = Channel.value(params.nuclear_ppdir)
// ch_nuclear_segdir = Channel.value(params.nuclear_segdir)
// ch_nuclear_weights = Channel.value(params.nuclear_weights_directory)
// ch_imctoolsdir = Channel.value(params.imctools_dir)

// NUCLEAR_PREPROCESS(ch_imctoolsdir, ch_nuclear_ppdir)


// Show help message
if (params.help) {
    helpMessage()
    exit 0
}

// Has the run name been specified by the user?
// this has the bonus effect of catching both -name and --name
custom_runName = params.name
if (!(workflow.runName ==~ /[a-z]+_[a-z]+/)) {
    custom_runName = workflow.runName
}

// Stage config files
ch_output_docs = file("$baseDir/docs/output.md", checkIfExists: true)
ch_output_docs_images = file("$baseDir/docs/images/", checkIfExists: true)

/*
 * Validate inputs
 */
if (params.input) {
    Channel
        .fromPath(params.input, checkIfExists: true)
        .map { it -> [ it.name.take(it.name.lastIndexOf('.')), it ] }
        .ifEmpty { exit 1, "Input file not found: ${params.input}" }
        .set { ch_mcd }
} else {
   exit 1, "Input file not specified!"
}

if (params.metadata)             { ch_metadata = file(params.metadata, checkIfExists: true) }                         else { exit 1, "Metadata csv file not specified!" }
if (params.full_stack_cppipe)    { ch_full_stack_cppipe = file(params.full_stack_cppipe, checkIfExists: true) }       else { exit 1, "CellProfiler full stack cppipe file not specified!" }
if (params.ilastik_stack_cppipe) { ch_ilastik_stack_cppipe = file(params.ilastik_stack_cppipe, checkIfExists: true) } else { exit 1, "Ilastik stack cppipe file not specified!" }
if (params.segmentation_cppipe)  { ch_segmentation_cppipe = file(params.segmentation_cppipe, checkIfExists: true) }   else { exit 1, "CellProfiler segmentation cppipe file not specified!" }

if (!params.skip_ilastik) {
    if (params.ilastik_training_ilp) {
        ch_ilastik_training_ilp = file(params.ilastik_training_ilp, checkIfExists: true) } else { exit 1, "Ilastik training ilp file not specified!" }
}

if (params.compensation_tiff) {
    Channel
        .fromPath(params.compensation_tiff, checkIfExists: true)
        .into { ch_compensation_full_stack;
                ch_compensation_ilastik_stack }
} else {
    Channel
        .empty()
        .into { ch_compensation_full_stack;
                ch_compensation_ilastik_stack }
}

// Plugins required for CellProfiler
Channel
    .fromPath(params.plugins, type: 'dir' , checkIfExists: true)
    .into { ch_preprocess_full_stack_plugin;
            ch_preprocess_ilastik_stack_plugin;
            ch_segmentation_plugin }

// AWS Batch settings
if (workflow.profile == 'awsbatch') {
  // AWSBatch sanity checking
  if (!params.awsqueue || !params.awsregion) exit 1, "Specify correct --awsqueue and --awsregion parameters on AWSBatch!"
  // Check outdir paths to be S3 buckets if running on AWSBatch
  // related: https://github.com/nextflow-io/nextflow/issues/813
  if (!params.outdir.startsWith('s3:')) exit 1, "Outdir not on S3 - specify S3 Bucket to run on AWSBatch!"
  // Prevent trace files to be stored on S3 since S3 does not support rolling files.
  if (workflow.tracedir.startsWith('s3:')) exit 1, "Specify a local tracedir or run without trace! S3 cannot be used for tracefiles."
}

// Header log info
log.info nfcoreHeader()
def summary = [:]
summary['Run Name']                     = custom_runName ?: workflow.runName
summary['Input Files']                  = params.input
summary['Metadata File']                = params.metadata
summary['Full Stack cppipe File']       = params.full_stack_cppipe
summary['Ilastik Stack cppipe File']    = params.ilastik_stack_cppipe
summary['Skip Ilastik Step']            = params.skip_ilastik ? 'Yes' : 'No'
if (params.compensation_tiff) summary['Compensation Tiff']    = params.compensation_tiff
if (!params.skip_ilastik) summary['Ilastik Training ilp File'] = params.ilastik_training_ilp
summary['Segmentation cppipe File']     = params.segmentation_cppipe
summary['Max Resources']    = "$params.max_memory memory, $params.max_cpus cpus, $params.max_time time per job"
if (workflow.containerEngine) summary['Container'] = "$workflow.containerEngine - $workflow.container"
summary['Output Dir']                   = params.outdir
summary['Launch Dir']                   = workflow.launchDir
summary['Working Dir']                  = workflow.workDir
summary['Script Dir']                   = workflow.projectDir
summary['User']                         = workflow.userName
summary['Config Profile']               = workflow.profile
if (params.config_profile_description) summary['Config Description'] = params.config_profile_description
if (params.config_profile_contact)     summary['Config Contact']     = params.config_profile_contact
if (params.config_profile_url)         summary['Config URL']         = params.config_profile_url
if (workflow.profile.contains('awsbatch')) {
  summary['AWS Region']                = params.awsregion
  summary['AWS Queue']                 = params.awsqueue
  summary['AWS CLI']                   = params.awscli
}
if (params.email || params.email_on_fail) {
  summary['E-mail Address']     = params.email
  summary['E-mail on failure']  = params.email_on_fail
}
log.info summary.collect { k,v -> "${k.padRight(25)}: $v" }.join("\n")
log.info "-\033[2m--------------------------------------------------\033[0m-"

// Check the hostnames against configured profiles
checkHostname()



// Function to get list of [sample_id,roi_id,path_to_file]
def flatten_tiff(ArrayList channel) {
    def sample = channel[0]
    def file_list = channel[1]
    def new_array = []
    for (int i=0; i<file_list.size(); i++) {
        def item = []
        item.add(sample)
        item.add(file_list[i].getParent().getParent().getName())
        item.add(file_list[i])
        new_array.add(item)
    }
    return new_array
}

// Group full stack files by sample and roi_id
ch_full_stack_tiff
    .map { flatten_tiff(it) }
    .flatten()
    .collate(3)
    .groupTuple(by: [0,1])
    .map { it -> [ it[0], it[1], it[2].sort() ] }
    .set { ch_full_stack_tiff }

// Group ilastik stack files by sample and roi_id
ch_ilastik_stack_tiff
    .map { flatten_tiff(it) }
    .flatten()
    .collate(3)
    .groupTuple(by: [0,1])
    .map { it -> [ it[0], it[1], it[2].sort() ] }
    .set { ch_ilastik_stack_tiff }

// Group ch_dna1 files by sample and roi_id
ch_dna1
    .map { flatten_tiff(it) }
    .flatten()
    .collate(3)
    .groupTuple(by: [0,1])
    .map { it -> [ it[0], it[1], it[2].sort() ] }
    .set { ch_dna1 }

// Group ch_dna2 files by sample and roi_id
ch_dna2
    .map { flatten_tiff(it) }
    .flatten()
    .collate(3)
    .groupTuple(by: [0,1])
    .map { it -> [ it[0], it[1], it[2].sort() ] }
    .set { ch_dna2 }

// Group ch_Ru files by sample and roi_id
ch_Ru
    .map { flatten_tiff(it) }
    .flatten()
    .collate(3)
    .groupTuple(by: [0,1])
    .map { it -> [ it[0], it[1], it[2].sort() ] }
    .set { ch_Ru }

ch_full_stack_tiff.into { ch_full_stack_tiff; ch_full_stack_phe }
















/*
 * Completion e-mail notification
 */
workflow.onComplete {

    // Set up the e-mail variables
    def subject = "[nf-core/imcyto] Successful: $workflow.runName"
    if (!workflow.success) {
        subject = "[nf-core/imcyto] FAILED: $workflow.runName"
    }
    def email_fields = [:]
    email_fields['version'] = workflow.manifest.version
    email_fields['runName'] = custom_runName ?: workflow.runName
    email_fields['success'] = workflow.success
    email_fields['dateComplete'] = workflow.complete
    email_fields['duration'] = workflow.duration
    email_fields['exitStatus'] = workflow.exitStatus
    email_fields['errorMessage'] = (workflow.errorMessage ?: 'None')
    email_fields['errorReport'] = (workflow.errorReport ?: 'None')
    email_fields['commandLine'] = workflow.commandLine
    email_fields['projectDir'] = workflow.projectDir
    email_fields['summary'] = summary
    email_fields['summary']['Date Started'] = workflow.start
    email_fields['summary']['Date Completed'] = workflow.complete
    email_fields['summary']['Pipeline script file path'] = workflow.scriptFile
    email_fields['summary']['Pipeline script hash ID'] = workflow.scriptId
    if (workflow.repository) email_fields['summary']['Pipeline repository Git URL'] = workflow.repository
    if (workflow.commitId) email_fields['summary']['Pipeline repository Git Commit'] = workflow.commitId
    if (workflow.revision) email_fields['summary']['Pipeline Git branch/tag'] = workflow.revision
    email_fields['summary']['Nextflow Version'] = workflow.nextflow.version
    email_fields['summary']['Nextflow Build'] = workflow.nextflow.build
    email_fields['summary']['Nextflow Compile Timestamp'] = workflow.nextflow.timestamp

    // Check if we are only sending emails on failure
    email_address = params.email
    if (!params.email && params.email_on_fail && !workflow.success) {
        email_address = params.email_on_fail
    }

    // Check if we are only sending emails on failure
    email_address = params.email
    if (!params.email && params.email_on_fail && !workflow.success) {
        email_address = params.email_on_fail
    }

    // Render the TXT template
    def engine = new groovy.text.GStringTemplateEngine()
    def tf = new File("$baseDir/assets/email_template.txt")
    def txt_template = engine.createTemplate(tf).make(email_fields)
    def email_txt = txt_template.toString()

    // Render the HTML template
    def hf = new File("$baseDir/assets/email_template.html")
    def html_template = engine.createTemplate(hf).make(email_fields)
    def email_html = html_template.toString()

    // Render the sendmail template
    def smail_fields = [ email: email_address, subject: subject, email_txt: email_txt, email_html: email_html, baseDir: "$baseDir"]
    def sf = new File("$baseDir/assets/sendmail_template.txt")
    def sendmail_template = engine.createTemplate(sf).make(smail_fields)
    def sendmail_html = sendmail_template.toString()

    // Send the HTML e-mail
    if (email_address) {
        try {
            if (params.plaintext_email) { throw GroovyException('Send plaintext e-mail, not HTML') }
            // Try to send HTML e-mail using sendmail
            [ 'sendmail', '-t' ].execute() << sendmail_html
            log.info "[nf-core/imcyto] Sent summary e-mail to $email_address (sendmail)"
        } catch (all) {
            // Catch failures and try with plaintext
            [ 'mail', '-s', subject, email_address ].execute() << email_txt
            log.info "[nf-core/imcyto] Sent summary e-mail to $email_address (mail)"
        }
    }

    // Write summary e-mail HTML to a file
    def output_d = new File("${params.outdir}/pipeline_info/")
    if (!output_d.exists()) {
        output_d.mkdirs()
    }
    def output_hf = new File(output_d, "pipeline_report.html")
    output_hf.withWriter { w -> w << email_html }
    def output_tf = new File(output_d, "pipeline_report.txt")
    output_tf.withWriter { w -> w << email_txt }

    c_green = params.monochrome_logs ? '' : "\033[0;32m";
    c_purple = params.monochrome_logs ? '' : "\033[0;35m";
    c_red = params.monochrome_logs ? '' : "\033[0;31m";
    c_reset = params.monochrome_logs ? '' : "\033[0m";

    if (workflow.stats.ignoredCount > 0 && workflow.success) {
        log.info "-${c_purple}Warning, pipeline completed, but with errored process(es) ${c_reset}-"
        log.info "-${c_red}Number of ignored errored process(es) : ${workflow.stats.ignoredCount} ${c_reset}-"
        log.info "-${c_green}Number of successfully ran process(es) : ${workflow.stats.succeedCount} ${c_reset}-"
    }

    if (workflow.success) {
        log.info "-${c_purple}[nf-core/imcyto]${c_green} Pipeline completed successfully${c_reset}-"
    } else {
        checkHostname()
        log.info "-${c_purple}[nf-core/imcyto]${c_red} Pipeline completed with errors${c_reset}-"
    }

}


