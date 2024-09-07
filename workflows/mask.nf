workflow MASK_WF {
    take:
    ch_img

    main:
    // download cellpose models
    ch_models = DOWNLOAD_CELLPOSE_MODELS()
    // mask each image
    ch_img_mask = MASK(ch_img, ch_models.collect())
    
    emit:
    img_orig = ch_img_mask.img_orig // original images
    img_masked = ch_img_mask.masked // masked images
    img_masks = ch_img_mask.masks   // image masks
    mask_log = ch_img_mask.log       // log files
}

// Select/format the output files
def saveAsMask(filename) {
    if (filename.endsWith('_masks.tif') || filename.endsWith('_full_minprojection.tif') || filename.endsWith('.log')){
        return filename
    } 
    return null
}

// Mask an image using cellpose 
process MASK {
    publishDir file(params.output_dir) / "mask", mode: "copy", overwrite: true, saveAs: { filename -> saveAsMask(filename) } 
    conda "envs/cellpose.yml"
    label "process_medium_mem"

    input:
    tuple val(img_basename), path(img_file)
    path "models/*"

    output:
    tuple path("frate.txt"), path("*masked.tif"), emit: masked    // masked image
    path img_file,                                emit: img_orig  // original image
    path "*masks.tif",                            emit: masks     // image masks
    path "*masked-plot.tif",                      emit: masked_plot, optional: true
    path "*minprojection.tif",                    emit: minprojection, optional: true
    path "${img_basename}.log",                   emit: log  

    script:
    def use_2d = params.use_2d == true ? "--use-2d" : ""
    """
    # set local models path
    export CELLPOSE_LOCAL_MODELS_PATH=models
    # run cellpose
    mask.py --file-type ${params.file_type} ${use_2d} ${img_file} > ${img_basename}.log 2>&1
    """

    stub:
    """
    touch frate.txt image_masked.tif image_masks.tif ${img_basename}.log image_full_minprojection.tif
    """
}

// Download cellpose models
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

    stub:
    """
    mkdir -p models
    touch models/blank.txt
    """
}