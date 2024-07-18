workflow MASK_WF {
    take:
    ch_img

    main:
    //if(params.use_2d != true){

    // download cellpose models
    ch_models = DOWNLOAD_CELLPOSE_MODELS()
    // mask each image
    ch_img_mask = MASK(ch_img, ch_models.collect())
        
        
        //ch_img_mask = MASK_WF.out.mask
    /*
    } else {
        //ch_img_mask = ch_img
        ch_img_mask = NO_MASK(ch_img)
    }  
    */
    
    emit:
    mask = ch_img_mask.mask
}

process MASK {
    input:
    path img
    path "models/*"

    output:
    tuple env(FRATE), path("*_masked.tif"),  emit: mask
    path "*_masked-plot.tif",                emit: mask_plot

    script:
    def use_2d = params.use_2d == true ? "--use-2d" : ""
    """
    export CELLPOSE_LOCAL_MODELS_PATH=models
    mask.py --file-type ${params.file_type} ${use_2d} $img
    source frate.sh
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