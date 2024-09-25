workflow INPUT_WF {
    // Status
    println("File type: ${params.file_type}")
    if (params.test_image_count.toInteger() > 0){
        def image_str = params.test_image_count.toInteger() > 1 ? "images" : "image"
        println "Selecting ${params.test_image_count} random test ${image_str}"
    } else if (params.test_image_names != null){
        println "Selecting test images: ${params.test_image_names}"
    }

    // Format input file name
    FORMAT_INPUT(params.input_dir)
    ch_img = FORMAT_INPUT.out.img.flatten()
    ch_groups = FORMAT_INPUT.out.groups

    // Concatenate the images per-group, if the file type is 'moldev'
    if (params.file_type == "moldev"){
        // Each group will be processed separately
        /// create tuple of ch_img
        ch_img = ch_img
            .map{ img_path -> tuple(img_path, img_path.toString()) }
        /// Read the CSV file, join with image paths, and group by the 'group' field
        ch_groups = ch_groups
            .splitCsv(header: true)  // Read the CSV file and interpret it
            .map{ row -> tuple(row.group_name, row.file_path) }
            .join(ch_img, by: 1)
            .groupTuple(by: 1)
            .map{ tuple(it[1], it[2]) }
        
        // Concatenate the images by group
        ch_img = MOLDEV_CONCAT(ch_groups).img.flatten()
        ch_cat_log = MOLDEV_CONCAT.out.log
    } else {
        ch_cat_log = channel.empty()
    }

    // Check that the channel is not empty
    ch_img = ch_img.ifEmpty { 
        error "No image files found in the input directory: ${params.input_dir}" 
    }

    // Create tuple of (base_name, image_path) for each image
    ch_img = ch_img.map{ img_path -> tuple(img_path.baseName, img_path) }

    emit:
    img = ch_img 
    fmt_log = FORMAT_INPUT.out.log
    cat_log = ch_cat_log
}

process MOLDEV_CONCAT {
    conda "envs/cellpose.yml"
    label "process_medium_mem"

    input:
    tuple val(baseName), path(imagePaths)

    output:
    path "output/${baseName}_full.tif", emit: img
    path "${baseName}_moldev-cat.log",    emit: log

    script:
    """
    concatenate_moldev_files.py \\
      --output output/${baseName}_full.tif \\
      $imagePaths \\
      > ${baseName}_moldev-cat.log 2>&1
    """

    stub:
    """
    touch ${baseName}_full.tif "${baseName}_moldev-cat.log"
    """
}

process FORMAT_INPUT{
    conda "envs/cellpose.yml"

    input:
    path input_dir

    output:
    path "FMT_OUTPUT/*",     emit: img
    path "groups.csv",       emit: groups
    path "format_input.log", emit: log

    script:
    def test_image_names = params.test_image_names == null ? "" : "--test-image-names \"${params.test_image_names}\""
    def test_image_count = params.test_image_count == 0 ? "" : "--test-image-count ${params.test_image_count}"
    """
    format_input.py $test_image_names $test_image_count \\
      --file-type $params.file_type \\
      $input_dir \\
      > format_input.log 2>&1
    """

    stub:
    """
    OUTDIR="FMT_OUTPUT"
    mkdir -p $OUTDIR
    touch groups.csv format_input.log $OUTDIR/TEST1.tif $OUTDIR/TEST2.tif
    """
}
 
