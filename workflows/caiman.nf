workflow CAIMAN_WF {
    take:
    ch_img
    ch_img_mask

    main:
    // Run CAIMAN
    CAIMAN(ch_img, ch_img_mask)

    // run calc_dff_f0
    CALC_DFF_F0(CAIMAN.out.cnm_A, CAIMAN.out.img, CAIMAN.out.img_mask)
}



process CALC_DFF_F0 {
    conda "envs/caiman.yml"
   
    input:
    path cnm_A
    path img
    path img_mask

    output:
    path "output/*"

    script:
    """
    calc_dff_f0.py \
      --file-type ${params.file_type} \
      --threshold-percentile ${params.p_th} \
      $cnm_A $img $img_mask
    """
}

def saveAsCaiman(file){
    return file.split("/").last()
}

process CAIMAN {
    publishDir file(params.output_dir) / "caiman", mode: "copy", overwrite: true, saveAs: { file -> saveAsCaiman(file) }
    conda "envs/caiman.yml"
    label "process_medium"

    input:
    path img
    tuple path(frate), path(img_mask)

    output:
    path img,                         emit: img
    path img_mask,                    emit: img_mask
    path "caiman_output/*_cnm_A.npy", emit: cnm_A
    path "${img_mask.baseName}.log",  emit: log

    script:
    def img_mask_basename = img_mask.baseName
    """
    # set the input paths
    export CAIMAN_DATA=caiman_data
    rm -rf \$CAIMAN_DATA && mkdir -p \${CAIMAN_DATA}/temp
    cp $img_mask \${CAIMAN_DATA}/temp/

    # run the caiman process
    caiman_run.py -p $task.cpus $frate $img_mask > "${img_mask_basename}.log" 2>&1
    """
}

/*
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