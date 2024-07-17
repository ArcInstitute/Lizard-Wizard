workflow CAIMAN_WF {
    take:
    ch_img_mask

    main:
    // Run the CAIMAN process
    CAIMAN(ch_img_mask)

}

process CAIMAN {
    label "process_medium"

    input:
    path file("caiman_temp") / img

    output:
    path "caiman_output"

    script:
    """
    # set the input paths
    export CAIMAN_DATA=caiman_data
    rm -rf $CAIMAN_DATA && mkdir -p ${CAIMAN_DATA}/temp
    cp $img ${CAIMAN_DATA}/temp/

    # run the caiman process
    caiman_run.py -p $task.cpus $img
    """
}