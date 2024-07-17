// Subworkflows
include { INPUT } from './workflows/input.nf'

// Main workflow
workflow {
    // Create the image channel
    ch_img = INPUT()
    
}


// On complete
workflow.onComplete {
    println "Pipeline completed at: $workflow.complete"
    println "Execution status: ${ workflow.success ? 'OK' : 'failed' }"
}
