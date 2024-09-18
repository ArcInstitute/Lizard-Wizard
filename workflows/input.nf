workflow INPUT_WF {
    // Status
    println("File type: ${params.file_type}")
    if (params.test_image_count.toInteger() > 0){
        def image_str = params.test_image_count.toInteger() > 1 ? "images" : "image"
        println "Selecting ${params.test_image_count} random test ${image_str}"
    } else if (params.test_image_names != null){
        println "Selecting test images: ${params.test_image_names}"
    }

    // Create a channel of input images
    if(params.file_type == "zeiss"){
        // Zeiss file type
        ch_img = Channel.fromPath(file(params.input_dir) / "**.czi", checkIfExists: true)
        // Filter the images by the test_image_count or test_image_names
        /// Select random images
        if (params.test_image_count.toInteger() > 0){
            ch_img = ch_img.randomSample(params.test_image_count.toInteger())
        }
        /// Select specific images
        else if(params.test_image_names != null){
            // Convert the string to a list of basenames
            def test_image_basenames = params.test_image_names.split(",")
    
            // Select images from the list of images by matching the basename
            ch_img = ch_img.collect().map{ list -> 
                list.findAll { file -> 
                    def basename = file.getBaseName()
                    test_image_basenames.contains(basename)
                }
            }.flatten()
        } 
        // Create empty channels for the logs
        ch_grp_log = Channel.empty()
        ch_cat_log = Channel.empty()
    } else if (params.file_type == "moldev"){
        // Group by basename and create a csv file
        MOLDEV_GROUP(params.input_dir).csv
        ch_grp_tbl = MOLDEV_GROUP.out.csv
        ch_grp_log = MOLDEV_GROUP.out.log
        // Read the CSV file and group by the 'group' field
        ch_img = ch_grp_tbl
            .splitCsv(header: true)  // Read the CSV file and interpret it
            .map{ row -> tuple(row.group_name, row.file_path) }
            .groupTuple()
        // Concatenate the images by group
        MOLDEV_CONCAT(ch_img, params.input_dir).img.flatten()
        ch_img = MOLDEV_CONCAT.out.img.flatten()
        ch_cat_log = MOLDEV_CONCAT.out.log
    } else {
        // Raise error if the file_type is not supported
        error "Unsupported file_type: '${params.file_type}'. Supported types are 'zeiss' and 'moldev'."
    }
    // Check that the channel is not empty
    ch_img = ch_img.ifEmpty { error "No image files found in the input directory: ${params.input_dir}" }

    // Create tuple of (base_name, image_path) for each image
    ch_img = ch_img.map{ image_path -> tuple(image_path.baseName, image_path) }

    emit:
    img = ch_img 
    grp_log = ch_grp_log
    cat_log = ch_cat_log
}


// Load and concatenate Molecular Devices images
process MOLDEV_CONCAT {
    conda "envs/cellpose.yml"
    label "process_medium_mem"

    input:
    tuple val(baseName), val(imagePaths)
    path input_dir

    output:
    path "${baseName}_full.tif", emit: img
    path "${baseName}_moldev-cat.log",      emit: log

    script:
    imagePaths = imagePaths.join(" ") // Concatenate the image path list
    """
    concatenate_moldev_files.py \\
      --output ${baseName}_full.tif \\
      $imagePaths > "${baseName}_moldev-cat.log" 2>&1
    """

    stub:
    """
    touch ${baseName}_full.tif "${baseName}_moldev-cat.log"
    """
}

// Group Molecular Devices images
process MOLDEV_GROUP {
    conda "envs/cellpose.yml"

    input:
    path input_dir

    output:
    path "file_groups.csv",  emit: csv
    path "moldev-group.log", emit: log

    script:
    def test_image_names = params.test_image_names == null ? "" : "--test-image-names ${params.test_image_names}"
    def test_image_count = params.test_image_count == 0 ? "" : "--test-image-count ${params.test_image_count}"
    """
    group_moldev_files.py $test_image_names $test_image_count \
      $input_dir > file_groups.csv 2> moldev-group.log
    """

    stub:
    """
    touch file_groups.csv moldev-group.log
    """
}



