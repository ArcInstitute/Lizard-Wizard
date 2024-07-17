workflow MASK {
    take:
    ch_img

    main:
    // download cellpose models
    ch_models = DOWNLOAD_CELLPOSE_MODELS()
    // mask each image
    ch_img_mask = MASK_IMAGE(ch_img, ch_models.collect())

    //ch_img_mask.mask.view()
    //ch_img_mask.mask_plot.view()

    emit:
    mask = ch_img_mask.mask
    mask_plot = ch_img_mask.mask_plot
}

process MASK_IMAGE {
    input:
    path img
    path "models/*"

    output:
    path "*_masked.tif",      emit: mask
    path "*_masked-plot.tif", emit: mask_plot

    script:
    """
    export CELLPOSE_LOCAL_MODELS_PATH=models
    mask.py --file-type ${params.file_type} $img
    """
}

process DOWNLOAD_CELLPOSE_MODELS {
    output:
    path "models/*"

    script:
    """
    export CELLPOSE_LOCAL_MODELS_PATH=models
    download_cellpose_models.py models
    """
}