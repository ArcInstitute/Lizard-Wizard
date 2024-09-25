workflow SIMULATE_WF {
    // simulate data
    SIMULATE_EVENTS()
    ch_img = SIMULATE_EVENTS.out.tif

    // Create tuple of (base_name, image_path) for each image
    ch_img = ch_img.map{ img_path -> tuple(img_path.baseName, img_path) }

    emit:
    img = ch_img
    fmt_log = channel.empty()
    cat_log = channel.empty()
}

process SIMULATE_EVENTS {
    publishDir file(params.output_dir) / "simulate", mode: "copy", overwrite: true
    conda "envs/cellpose.yml"

    output:
    path "synthetic_puffs_movie.tiff",         emit: tif
    path "synthetic_puffs_puff_positions.csv", emit: csv

    script:
    """
    simulate_events.py ${baseDir}/data/synthetic_puffs_movie.tiff
    """

    stub:
    """
    touch synthetic_puffs_movie.tiff synthetic_puffs_puff_positions.csv
    """
}  