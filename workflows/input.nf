workflow INPUT {
    if(params.file_type == "zeiss"){
        // Zeiss file type
        ch_img = Channel.fromPath(file(params.input_dir) / "**.czi", checkIfExists: true)
    } else if (params.file_type == "moldev"){
        // Molecular Divices file type
        ch_img = MOLDEV_CONCAT()
    } else {
        // raise error if the file_type is not supported
        error "Unsupported file_type: '${params.file_type}'. Supported types are 'zeiss' and 'moldev'."
    }
    // check that the channel is not empty
    ch_img = ch_img.ifEmpty { error "No image files found in the input directory: ${params.input_dir}" }

    // debug
    ch_img.view() 

    emit:
    ch_img
}

process MOLDEV_CONCAT {
    label "process_low"

    output:
    path "tiff_combined/*.tif"

    script:
    def test_image_nums = params.test_image_nums == null ? "" : "--test-image-nums ${params.test_image_nums}"
    def test_image_count = params.test_image_count == 0 ? "" : "--test-image-count ${params.test_image_count}"
    """
    concatenate_moldev_files.py ${test_image_nums} ${test_image_count} \
      --output-dir tiff_combined ${params.input_dir}
    """
}