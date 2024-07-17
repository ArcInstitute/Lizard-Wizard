// Subworkflows
include { INPUT_WF } from './workflows/input.nf'
include { MASK_WF } from './workflows/mask.nf'
include { CAIMAN_WF } from './workflows/caiman.nf'

// Main workflow
workflow {
    // Create the image channel
    ch_img = INPUT_WF()

    // Create the mask channel
    if(params.use_2d != true){
        MASK_WF(ch_img)
        ch_img_mask = MASK_WF.out.mask
    } else {
        ch_img_mask = ch_img
    }  

    // Run Caiman
    CAIMAN_WF(ch_img_mask)

}


// On complete
workflow.onComplete {
    println "Pipeline completed at: $workflow.complete"
    println "Execution status: ${ workflow.success ? 'OK' : 'failed' }"
}
