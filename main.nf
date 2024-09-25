// Subworkflows
include { SIMULATE_WF } from './workflows/simulate.nf'
include { INPUT_WF } from './workflows/input.nf'
include { MASK_WF } from './workflows/mask.nf'
include { CAIMAN_WF } from './workflows/caiman.nf'
include { SUMMARY_WF } from './workflows/summary.nf'

// Main workflow
workflow {
    def use_2d = params.use_2d
    // Create the image channel
    if (params.simulate == true) {
        // just simulates 2d data
        use_2d = true
        // run the simulation workflow
        SIMULATE_WF()
        ch_img = SIMULATE_WF.out.img
        ch_fmt_log = SIMULATE_WF.out.fmt_log
        ch_cat_log = SIMULATE_WF.out.cat_log
    } else {
        INPUT_WF()
        ch_img = INPUT_WF.out.img
        ch_fmt_log = INPUT_WF.out.fmt_log
        ch_cat_log = INPUT_WF.out.cat_log
    }

    // Create the mask channel
    MASK_WF(ch_img, channel.of(use_2d))

    // Run Caiman
    CAIMAN_WF(
        MASK_WF.out.img_orig, 
        MASK_WF.out.img_masked,
        MASK_WF.out.img_masks
    )
    
    // Summarize log files
    SUMMARY_WF(
        MASK_WF.out.img_masked,
        ch_fmt_log,
        ch_cat_log,
        MASK_WF.out.mask_log,
        CAIMAN_WF.out.caiman_log,
        CAIMAN_WF.out.calc_dff_f0_log
    )
}

// On complete
workflow.onComplete {
    println "Pipeline completed at: $workflow.complete"
    println "Execution status: ${ workflow.success ? 'OK' : 'failed' }"
}
