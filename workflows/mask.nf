workflow MASK_WF {
    take:
    ch_img

    main:
    // download cellpose models
    ch_models = DOWNLOAD_CELLPOSE_MODELS()
    // mask each image
    ch_img_mask = MASK(ch_img, ch_models.collect())
    
    emit:
    mask = ch_img_mask.masked
    img = ch_img_mask.img
}

def saveAsMask(file) {
    (file.size() > 0 && !file.endsWith('.txt')) ? file : null
}

process MASK {
    publishDir file(params.output_dir) / "mask", mode: "copy", overwrite: true, saveAs: { file -> saveAsMask(file) }
    conda "envs/cellpose.yml"
    label "process_medium_mem"

    input:
    tuple val(img_basename), path(img_file)
    path "models/*"

    output:
    tuple path("frate.txt"), path("*masked.tif"), emit: masked
    path img_file,                                emit: img
    path "*masked-plot.tif",                      emit: masked_plot, optional: true
    path "*masks.tif",                            emit: masks, optional: true
    path "*minprojection.tif",                    emit: minprojection, optional: true
    path "${img_basename}.log",                   emit: log  

    script:
    def use_2d = params.use_2d == true ? "--use-2d" : ""
    """
    # set local models path
    export CELLPOSE_LOCAL_MODELS_PATH=models
    # run cellpose
    mask.py --file-type ${params.file_type} ${use_2d} ${img_file} > "${img_basename}.log" 2>&1
    """
}

process DOWNLOAD_CELLPOSE_MODELS {
    conda "envs/cellpose.yml"

    output:
    path "models/*"

    script:
    """
    # set local models path
    export CELLPOSE_LOCAL_MODELS_PATH=models
    # download cellpose models to the local path
    download_cellpose_models.py models
    """
}