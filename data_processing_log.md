Nick's data processing log.
Consider this log as a set of examples of how to run the pipeline.

## Spot check 

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -N nick.youngblut@arcinstitute.org \
  --input_dir /large_storage/multiomics/projects/lizard_wizard/test_data/Calcium_AAV-GCAMP_6wk_20240416 \
  --output_dir /large_storage/multiomics/projects/lizard_wizard/test_output/Calcium_AAV-GCAMP_6wk_20240416 \
  --test_image_count 2
```

# `Calcium_AAV-GCAMP_6wk_20240416`

## Spot check 

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -N nick.youngblut@arcinstitute.org \
  --input_dir /large_storage/multiomics/projects/lizard_wizard/test_data/Calcium_AAV-GCAMP_6wk_20240416 \
  --output_dir /large_storage/multiomics/projects/lizard_wizard/test_output/Calcium_AAV-GCAMP_6wk_20240416 \
  --test_image_count 2
```

# `CMTC-Sph07162024-Plate3-HYB`

## Spot check

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -N nick.youngblut@arcinstitute.org \
  --input_dir /large_storage/multiomics/projects/lizard_wizard/test_data/CMTC-Sph07162024-Plate3-HYB \
  --output_dir /large_storage/multiomics/projects/lizard_wizard/test_output/CMTC-Sph07162024-Plate3-HYB \
  --test_image_count 3
```


## Full run

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -N nick.youngblut@arcinstitute.org \
  --input_dir /large_storage/multiomics/projects/lizard_wizard/test_data/CMTC-Sph07162024-Plate3-HYB \
  --output_dir /large_storage/multiomics/projects/lizard_wizard/test_output/CMTC-Sph07162024-Plate3-HYB \
  -resume
```


# `CMTC-Sph0762024-Plate1`

* data type: moldev-3d

## Spot check

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -N nick.youngblut@arcinstitute.org \
  --input_dir /large_storage/multiomics/projects/lizard_wizard/test_data/CMTC-Sph0762024-Plate1 \
  --output_dir /large_storage/multiomics/projects/lizard_wizard/test_output/CMTC-Sph0762024-Plate1 \
  --test_image_count 3
```


## Full run

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -N nick.youngblut@arcinstitute.org \
  --input_dir /large_storage/multiomics/projects/lizard_wizard/test_data/CMTC-Sph0762024-Plate1 \
  --output_dir /large_storage/multiomics/projects/lizard_wizard/test_output/CMTC-Sph0762024-Plate1 \
  -resume
```
