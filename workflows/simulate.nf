workflow SIMULATE_WF {
    // Simulate data
    SIMULATE_EVENTS()

    // Create tuple of (base_name, image_path) for each image
    ch_img = SIMULATE_EVENTS.out.tif.flatten().map{ img_path -> tuple(img_path.baseName, img_path) }

    emit:
    img = ch_img
    fmt_log = channel.empty()
    cat_log = channel.empty()
}

def saveAsBase(filename){
    return filename.split("/").last()
}

process SIMULATE_EVENTS {
    publishDir file(params.output_dir) / "simulation", mode: "copy", overwrite: true, saveAs: { filename -> saveAsBase(filename) }
    label "cellpose_env"

    output:
    path "output/*.tif", emit: tif
    path "output/*.csv", emit: csv

    script:
    """
    simulate_events.py \\
      --num_simulations ${params.num_simulations} \\
      --output_dir output \\
      ${baseDir}/data/synthetic_puffs_movie.tiff
    """

    stub:
    """
    mkdir -p output
    touch output/synthetic_puffs_sim-1_A01_s1_FITC.csv
    """
}  