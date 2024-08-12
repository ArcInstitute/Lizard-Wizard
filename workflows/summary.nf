workflow SUMMARY_WF {
    take:
    ch_mask_log
    ch_caiman_log

    main:
    // summarize logs
    LOG_SUMMARY(ch_mask_log, ch_caiman_log)
}

def saveAsSummary(file){
    return file.split("/").last()
}

process LOG_SUMMARY {
    publishDir file(params.output_dir) / "summary", mode: "copy", overwrite: true, saveAs: { file -> saveAsSummary(file) }
    conda "envs/summary.yml"
    secret "OPENAI_API_KEY"

    input:
    path mask_log
    path caiman_log

    output:
    path "output/*.md"

    script:
    """
    summarize_logs.py $mask_log $caiman_log
    """
}