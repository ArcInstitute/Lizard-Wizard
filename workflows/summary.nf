workflow SUMMARY_WF {
    take:
    ch_grp_log
    ch_cat_log
    ch_mask_log
    ch_caiman_log

    main:
    // summarize logs
    if("${secrets.OPENAI_API_KEY}" != "null"){
        LOG_SUMMARY(
            ch_grp_log.collect(),
            ch_cat_log.collect(),
            ch_mask_log.collect(), 
            ch_caiman_log.collect()
        )
    }
}

// Select/format the output files
def saveAsSummary(filename){
    return filename.split("/").last()
}

process LOG_SUMMARY {
    publishDir file(params.output_dir) / "log_summary", mode: "copy", overwrite: true, saveAs: { filename -> saveAsSummary(filename) }
    conda "envs/summary.yml"
    secret "OPENAI_API_KEY"

    input:
    path grp_log
    path cat_log
    path mask_log
    path caiman_log

    output:
    path "output/*.md",   emit: md
    path "output/*.html", emit: html

    script:
    """
    summarize_logs.py --model $params.llm $grp_log $cat_log $mask_log $caiman_log
    """

    stub:
    """
    mkdir -p output
    touch output/summary.md
    """
}