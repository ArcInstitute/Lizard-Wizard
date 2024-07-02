workflow SAMPLES_SHEET {
    // load input dir
    ch_input_dir = Channel.fromPath(params.input_dir, checkIfExists: true)
    // create sample table from input dir
    ch_samples_sheet = CREATE_SAMPLES_SHEET(ch_input_dir)
    
    // load samples sheet as channel
    ch_samples = ch_samples_sheet
      .splitCsv(sep: ",", header: true)
      .map { row -> return [row.Sample_ID, row.File_Path] }
    emit:
    ch_samples
}

process CREATE_SAMPLE_SHEET {
  input:
  path input_dir

  output:
  path "samples.csv"

  script:
  """
  create-sample-sheet.py ${input_dir} > samples.csv
  """
}
