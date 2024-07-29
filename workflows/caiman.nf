workflow CAIMAN_WF {
    take:
    ch_img_mask

    main:
    // Run the CAIMAN process
    CAIMAN(ch_img_mask)

}

process CAIMAN {
    conda "envs/caiman.yml"
    label "process_medium"

    input:
    tuple env(FRATE), path(img)

    output:
    path "caiman_output/*"

    script:
    """
    # set the input paths
    export CAIMAN_DATA=caiman_data
    rm -rf \$CAIMAN_DATA && mkdir -p \${CAIMAN_DATA}/temp
    cp $img \${CAIMAN_DATA}/temp/

    # run the caiman process
    caiman_run.py -p $task.cpus $img
    """
}

/*
    path "caiman_output/*_cnm_A.npy"
    path "caiman_output/*_cn_filter.npy"
    path "caiman_output/*_cn_filter.tif"
    path "caiman_output/*_cnm_C.npy"
    path "caiman_output/*_cnm_S.npy"
    path "caiman_output/*_cnm_idx.npy"
    path "caiman_output/*_masked_pnr_filter.npy"
    path "caiman_output/*_masked_pnr_filter.tif"
    path "caiman_output/correlation_pnr.png"
    path "caiman_output/histogram_pnr_cn_filter.png"
*/