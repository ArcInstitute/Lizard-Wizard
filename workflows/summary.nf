workflow SUMMARY_WF {
    take:
    ch_img_mask
    ch_grp_log
    ch_cat_log
    ch_mask_log
    ch_caiman_log
    ch_calc_dff_f0_log

    main:
    // Create metadata table
    /// Per-sample
    CREATE_PER_SAMPLE_METADATA_TABLE(ch_img_mask)
    /// Combine all samples
    CREATE_FINAL_METADATA_TABLE(
        CREATE_PER_SAMPLE_METADATA_TABLE.out.collect()
    )

    // summarize logs
    if("${secrets.OPENAI_API_KEY}" != "null"){
        // summarize moldev-concat logs
        LOG_SUMMARY_MOLDEV_CONCAT(
            ch_grp_log.collect(),
            ch_cat_log.collect()
        )
        def ch_moldev_concat_md = LOG_SUMMARY_MOLDEV_CONCAT.output.md.ifEmpty([])
        // summarize masking logs
        LOG_SUMMARY_MASK(
            ch_mask_log.collect()
        )
        // summarize caiman logs
        LOG_SUMMARY_CAIMAN(
            ch_caiman_log.collect(),
            ch_calc_dff_f0_log.collect()
        )
        // summarize final logs
        LOG_SUMMARY_FINAL(
            ch_moldev_concat_md,
            LOG_SUMMARY_MASK.output.md.collect(),
            LOG_SUMMARY_CAIMAN.output.md.collect()
        )
    }
}

process CREATE_FINAL_METADATA_TABLE {
    publishDir file(params.output_dir), mode: "copy", overwrite: true
    conda "envs/summary.yml"

    input:
    path metadata

    output:
    path "metadata.csv"

    script:
    """
    echo "Sample,Well,Frate" > metadata.csv
    cat $metadata >> metadata.csv
    """
}

process CREATE_PER_SAMPLE_METADATA_TABLE {
    conda "envs/summary.yml"

    input:
    tuple val(img_basename), path(frate), path(img_masked)

    output:
    path "${img_basename}.csv", emit: csv

    script:
    """
    create_metadata_table.py "$img_basename" $frate > "${img_basename}.csv"
    """
}

process LOG_SUMMARY_FINAL {
    publishDir file(params.output_dir) / "logs", mode: "copy", overwrite: true, saveAs: { filename -> saveAsSummary(filename) }
    conda "envs/summary.yml"
    secret "OPENAI_API_KEY"

    input:
    path moldev_concat_log
    path mask_log
    path caiman_log

    output:
    path "output/final_summary.md",   emit: md
    path "output/final_summary.html", emit: html

    script:
    """
    summarize_logs.py --model gpt-4o --final-summary \\
      $moldev_concat_log $mask_log $caiman_log
    """

    stub:
    """
    mkdir -p output
    touch output/final_summary.md
    """
}

process LOG_SUMMARY_CAIMAN {
    publishDir file(params.output_dir) / "logs" / "caiman", mode: "copy", overwrite: true, pattern: "*.{md,html}", saveAs: { filename -> saveAsSummary(filename) }
    publishDir file(params.output_dir) / "logs" / "caiman" / "logs", mode: "copy", overwrite: true, pattern: "*.{log}", saveAs: { filename -> saveAsSummary(filename) }
    conda "envs/summary.yml"
    secret "OPENAI_API_KEY"

    input:
    path caiman_log
    path calc_dff_f0_log

    output:
    path "output/caiman_summary.md",   emit: md
    path "output/caiman_summary.html", emit: html
    path caiman_log,                   emit: caiman_log
    path calc_dff_f0_log,              emit: calc_dff_f0_log

    script:
    """
    summarize_logs.py --model $params.llm \\
      --output-prefix caiman_summary \\
      $caiman_log $calc_dff_f0_log
    """

    stub:
    """
    mkdir -p output
    touch output/caiman_summary.md output/caiman_summary.html
    """
}

process LOG_SUMMARY_MASK {
    publishDir file(params.output_dir) / "logs" / "mask", mode: "copy", overwrite: true, pattern: "*.{md,html}", saveAs: { filename -> saveAsSummary(filename) }
    publishDir file(params.output_dir) / "logs" / "mask" / "logs", mode: "copy", overwrite: true, pattern: "*.{log}", saveAs: { filename -> saveAsSummary(filename) }
    conda "envs/summary.yml"
    secret "OPENAI_API_KEY"

    input:
    path mask_log

    output:
    path "output/mask_summary.md",   emit: md
    path "output/mask_summary.html", emit: html
    path mask_log,                   emit: mask_log

    script:
    """
    summarize_logs.py --model $params.llm \\
      --output-prefix mask_summary \\
      $mask_log
    """

    stub:
    """
    mkdir -p output
    touch output/mask_summary.md output/mask_summary.html
    """
}

process LOG_SUMMARY_MOLDEV_CONCAT {
    publishDir file(params.output_dir) / "logs" / "moldev-concat", mode: "copy", overwrite: true, pattern: "*.{md,html}", saveAs: { filename -> saveAsSummary(filename) }
    publishDir file(params.output_dir) / "logs" / "moldev-concat" / "logs", mode: "copy", overwrite: true, pattern: "*.{log}", saveAs: { filename -> saveAsSummary(filename) }
    conda "envs/summary.yml"
    secret "OPENAI_API_KEY"

    input:
    path grp_log
    path cat_log

    output:
    path "output/moldev-concat_summary.md",   emit: md
    path "output/moldev-concat_summary.html", emit: html
    path grp_log, emit: grp_log
    path cat_log, emit: cat_log

    script:
    """
    summarize_logs.py --model $params.llm \\
      --output-prefix moldev-concat_summary \\
      $grp_log $cat_log
    """

    stub:
    """
    mkdir -p output
    touch output/moldev-concat_summary.md output/moldev-concat_summary.html
    """
}

// Select/format the output files
def saveAsSummary(filename){
    return filename.split("/").last()
}
