workflow INPUT_WF {
    // Create a channel of input images
    if(params.file_type == "zeiss"){
        // Zeiss file type
        ch_img = Channel.fromPath(file(params.input_dir) / "**.czi", checkIfExists: true)
    } else if (params.file_type == "moldev"){
        // Molecular Divices file type
        ch_img = MOLDEV_CONCAT().img.flatten()
    } else {
        // Raise error if the file_type is not supported
        error "Unsupported file_type: '${params.file_type}'. Supported types are 'zeiss' and 'moldev'."
    }
    // Check that the channel is not empty
    ch_img = ch_img.ifEmpty { error "No image files found in the input directory: ${params.input_dir}" }

    // Spot Check: filter the images, if needed
    /// Note: for moldev, the spot check is done in the MOLDEV_CONCAT process
    if(params.file_type == "zeiss"){
        if (params.test_image_count.toInteger() > 0){
            // Select random images
            def image_str = params.test_image_count.toInteger() > 1 ? "images" : "image"
            println "Selecting ${params.test_image_count} random test ${image_str}"
            ch_img = ch_img.randomSample(params.test_image_count.toInteger())
        }
        else if(params.test_image_nums != null){
            println "Selecting test images: ${params.test_image_nums}"
            // Convert the string to a list of integers
            def test_image_nums = params.test_image_nums.split(",").collect{ it.toInteger() }
            // Select indices from the list of images
            ch_img = ch_img.collect().map{ list -> test_image_nums.collect{ list[it] } }.flatten()
        } 
    }

    // Create tuple of (base_name, image_path) for each image
    ch_img = ch_img.map{ image_path -> tuple(image_path.baseName, image_path) }

    emit:
    ch_img
}

// Load and concatenate Molecular Devices images
process MOLDEV_CONCAT {
    conda "envs/cellpose.yml"
    label "process_low"

    output:
    path "tiff_combined/*.tif",    emit: img
    path "moldev_img_concat.log",  emit: log

    script:
    def test_image_nums = params.test_image_nums == null ? "" : "--test-image-nums ${params.test_image_nums}"
    def test_image_count = params.test_image_count == 0 ? "" : "--test-image-count ${params.test_image_count}"
    """
    concatenate_moldev_files.py ${test_image_nums} ${test_image_count} \
      --threads $task.cpus \
      --output-dir tiff_combined ${params.input_dir} \
      > moldev_img_concat.log 2>&1
    """
}