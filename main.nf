// Subworkflows
include { INPUT_WF } from './workflows/input.nf'
include { MASK_WF } from './workflows/mask.nf'
include { CAIMAN_WF } from './workflows/caiman.nf'
include { SUMMARY_WF } from './workflows/summary.nf'

// Main workflow
workflow {
    // Create the image channel
    ch_img = INPUT_WF()

    // Create the mask channel
    MASK_WF(ch_img)

    // Run Caiman
    CAIMAN_WF(
        MASK_WF.out.img_orig, 
        MASK_WF.out.img_masked, 
        MASK_WF.out.img_masks
    )

    // Summarize log files
    SUMMARY_WF(
        MASK_WF.out.mask_log,
        CAIMAN_WF.out.caiman_log
    )
}


// On complete
workflow.onComplete {
    println "Pipeline completed at: $workflow.complete"
    println "Execution status: ${ workflow.success ? 'OK' : 'failed' }"
}

