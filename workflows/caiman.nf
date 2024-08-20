workflow CAIMAN_WF {
    take:
    ch_img_orig
    ch_img_masked
    ch_img_masks

    main:
    // Run CAIMAN
    CAIMAN(ch_img_orig, ch_img_masked, ch_img_masks)

    // run calc_dff_f0
    CALC_DFF_F0(
        CAIMAN.out.cnm_A, 
        CAIMAN.out.cnm_idx,
        CAIMAN.out.img_orig,
        CAIMAN.out.img_masks
    )

    emit:
    caiman_log = CAIMAN.out.log
}

// Helper function to format the output file name
def saveAsBase(filename){
    return filename.split("/").last()
}

// Calculate dF/F0
process CALC_DFF_F0 {
    publishDir file(params.output_dir) / "caiman_calc-dff-f0", mode: "copy", overwrite: true, saveAs: { filename -> saveAsBase(filename) }
    conda "envs/caiman.yml"
   
    input:
    path cnm_A
    path cnm_idx
    path img_orig
    path img_masks

    output:
    path "output/*"

    script:
    """
    calc_dff_f0.py \
      --file-type ${params.file_type} \
      --threshold-percentile ${params.p_th} \
      $cnm_A $cnm_idx $img_orig $img_masks
    """
    
    stub:
    """
    mkdir -p output
    touch output/blank.txt
    """
}

// Select/format the output files
def saveAsCaiman(filename){
    if (filename.endsWith('_masks.tif') || filename.endsWith('_cnm_A.npy') || filename.endsWith('_cnm_idx.npy') || filename.endsWith('.log')) {
        return saveAsBase(filename)
    }
    return null
}

// Run CaImAn
process CAIMAN {
    publishDir file(params.output_dir) / "caiman", mode: "copy", overwrite: true, saveAs: { filename -> saveAsCaiman(filename) }
    conda "envs/caiman.yml"
    label "process_medium"

    input:
    path img_orig
    tuple path(frate), path(img_masked)
    path img_masks

    output:
    path img_orig,                      emit: img_orig
    path img_masked,                    emit: img_masked
    path img_masks,                     emit: img_masks
    path "caiman_output/*_cnm_A.npy",   emit: cnm_A
    path "caiman_output/*_cnm_idx.npy", emit: cnm_idx
    path "${img_masked.baseName}.log",  emit: log

    script:
    def img_masked_basename = img_masked.baseName
    """
    # set the input paths
    export CAIMAN_DATA=caiman_data
    rm -rf \$CAIMAN_DATA && mkdir -p \${CAIMAN_DATA}/temp
    cp $img_masked \${CAIMAN_DATA}/temp/

    # run the caiman process
    caiman_run.py -p $task.cpus $frate $img_masked > "${img_masked_basename}.log" 2>&1
    """

    stub:
    """
    mkdir -p caiman_output
    touch caiman_output/${img_masked.baseName}_cnm_A.npy caiman_output/${img_masked.baseName}_cnm_idx.npy ${img_masked.baseName}.log
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