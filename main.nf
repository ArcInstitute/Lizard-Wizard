// Subworkflows
include { INPUT } from './workflows/input.nf'
include { MASK } from './workflows/mask.nf'
include { CAIMAN } from './workflows/caiman.nf'

// Main workflow
workflow {
    // Create the image channel
    ch_img = INPUT()

    // Create the mask channel
    if(params.use_2d != true){
        MASK(ch_img)
        ch_img_mask = MASK.out.mask
    } else {
        ch_img_mask = ch_img
    }  

    // Run Caiman
    CAIMAN(ch_img_mask)

}


// On complete
workflow.onComplete {
    println "Pipeline completed at: $workflow.complete"
    println "Execution status: ${ workflow.success ? 'OK' : 'failed' }"
}
