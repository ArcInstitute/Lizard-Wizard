workflow CAIMAN_WF {
    take:
    ch_img_orig
    ch_img_masked
    ch_img_masks

    main:
    // Run CAIMAN
    CAIMAN(ch_img_masked, ch_img_masks, ch_img_orig)

    // run calc_dff_f0
    CALC_DFF_F0(
        CAIMAN.out.img_masked,
        CAIMAN.out.img_masks,
        CAIMAN.out.img_orig,
        CAIMAN.out.cnm_A, 
        CAIMAN.out.cnm_idx
    )

    emit:
    caiman_log = CAIMAN.out.log
    calc_dff_f0_log = CALC_DFF_F0.out.log
}

// Helper function to format the output file name
def saveAsBase(filename){
    return filename.split("/")[-1]
}

// Calculate dF/F0
process CALC_DFF_F0 {
    publishDir file(params.output_dir) / "caiman_calc-dff-f0", mode: "copy", overwrite: true, saveAs: { filename -> saveAsBase(filename) }
    label "caiman_env"
    label "process_low_mem"
   
    input:
    tuple val(img_basename), path(frate), path(img_masked)
    path img_masks
    path img_orig
    path cnm_A
    path cnm_idx
    
    output:
    path "output/*_montage.png",                    emit: montage
    path "output/*_im-st.tif",                      emit: im_st
    path "output/*_montage-filtered.png",           emit: montage_filtered, optional: true
    path "output/*_f-dat.npy",                      emit: f_dat, optional: true
    path "output/*_dff-dat.npy",                    emit: dff_dat, optional: true
    path "output/*_df-f0-graph.png",                emit: df_f0_graph, optional: true
    path "${img_masked.baseName}_calc-diff-f0.log", emit: log

    script:
    """
    calc_dff_f0.py \\
      --file-type ${params.file_type} \\
      --p_th ${params.p_th} \\
      --f_baseline_perc ${params.f_baseline_perc} \\
      --win_sz ${params.win_sz} \\
      $cnm_A \\
      $cnm_idx \\
      $img_orig \\
      $img_masks \\
      2>&1 | tee ${img_masked.baseName}_calc-diff-f0.log
    """
    
    stub:
    """
    mkdir -p output
    touch output/blank.txt ${img_masked.baseName}_calc-diff-f0.log
    """
}

// Select/format the output files
def saveAsCaiman(filename){
    if (filename.endsWith('_cnm-A.npy') || 
        filename.endsWith('_cnm-C.npy') || 
        filename.endsWith('_cnm-S.npy') || 
        filename.endsWith('_cnm-idx.npy') || 
        filename.endsWith('_cn-filter.npy') || 
        filename.endsWith('_pnr-filter.npy') || 
        filename.endsWith('.log') || 
        filename.endsWith('.png')) {
        return saveAsBase(filename)
    }
    return null
}

// Run CaImAn
process CAIMAN {
    publishDir file(params.output_dir) / "caiman", mode: "copy", overwrite: true, saveAs: { filename -> saveAsCaiman(filename) }
    label "caiman_env"
    label "process_highest"

    input:
    tuple val(img_basename), path(frate), path(img_masked)
    path img_masks
    path img_orig

    output:
    tuple val(img_basename), path(frate), path(img_masked), emit: img_masked
    path img_masks,                                         emit: img_masks
    path img_orig,                                          emit: img_orig
    path "caiman_output/*_cnm-A.npy",                       emit: cnm_A
    path "caiman_output/*_cnm-C.npy",                       emit: cnm_C
    path "caiman_output/*_cnm-S.npy",                       emit: cnm_S
    path "caiman_output/*_cnm-idx.npy",                     emit: cnm_idx
    path "caiman_output/*_cn-filter.npy",                   emit: cn_filter
    path "caiman_output/*_pnr-filter.npy",                  emit: pnr_filter
    path "caiman_output/*_correlation-pnr.png",             emit: corr_pnr
    path "caiman_output/*_histogram-pnr-cn-filter.png",     emit: histo_pnr
    path "caiman_output/*_cnm-traces.png",                  emit: traces, optional: true
    path "caiman_output/*_cnm-denoised-traces.png",         emit: dn_traces, optional: true
    path "${img_masked.baseName}_caiman.log",               emit: log

    script:
    """
    # set the input paths
    export CAIMAN_DATA=caiman_data
    rm -rf \$CAIMAN_DATA && mkdir -p \${CAIMAN_DATA}/temp
    cp $img_masked \${CAIMAN_DATA}/temp/

    # run the caiman process
    caiman_run.py -p $task.cpus \\
      --decay_time $params.decay_time \\
      --gSig $params.gSig \\
      --rf $params.rf \\
      --min_SNR $params.min_SNR \\
      --r_values_min $params.r_values_min \\
      --tsub $params.tsub \\
      --ssub $params.ssub \\
      --min_corr $params.min_corr \\
      --min_pnr $params.min_pnr \\
      --ring_size_factor $params.ring_size_factor \\
      $frate $img_masked \\
      2>&1 | tee ${img_masked.baseName}_caiman.log
    """

    stub:
    """
    mkdir -p caiman_output
    touch caiman_output/${img_masked.baseName}_cnm_A.npy \\
      caiman_output/${img_masked.baseName}_cnm_idx.npy \\
      caiman_output/${img_masked.baseName}_correlation-pnr.png \\
      caiman_output/${img_masked.baseName}_histogram-pnr-cn-filter.png \\
      caiman_output/${img_masked.baseName}_cnm-traces.png \\
      caiman_output/${img_masked.baseName}_cnm-denoised-traces.png \\
      ${img_masked.baseName}_caiman.log
    """
}
