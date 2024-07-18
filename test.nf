process myTask {
  input:
  each x

  output:
  tuple val(x), env(FOO),  emit: method
  
  """
  echo $x > file
  FOO="TEST"
  """
}

workflow {
    methods = ['prot', 'dna', 'rna']

    receiver = myTask(methods)
    receiver.method.view()
}

