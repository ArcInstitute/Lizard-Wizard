// Subworkflows
include { SAMPLES_SHEET } from './workflows/samples_sheet.nf'

// Main workflow
workflow {
  SAMPLES_SHEET()
}


// On complete
workflow.onComplete {
    println "Pipeline completed at: $workflow.complete"
    println "Execution status: ${ workflow.success ? 'OK' : 'failed' }"
}
