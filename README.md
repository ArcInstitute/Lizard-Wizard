Lizard Wizard
=============

<img src="./img/lizard-wizard.png" alt="drawing" width="400"/>

**Calcium imaging analysis Nextflow pipeline for the Arc Institute.**

**Table of Contents**

1. [Installation](#installation)
    1. [Conda & mamba install](#conda--mamba-install)
    2. [Nextflow install](#nextflow-install)
    3. [Pipeline install](#pipeline-install)
        1. [Pipeline conda environments](#pipeline-conda-environments)
2. [Usage](#usage)
    1. [Parameters](#parameters)
    2. [Example Run](#example-run)
    3. [Test runs](#test-runs)
        1. [Local runs](#local-runs)
        2. [Slurm runs](#slurm-runs)
3. [Resources](#resources)
4. [Workflow](#workflow)
    1. [Input](#input)
    2. [Processing](#processing)


# Installation

## Conda & mamba install

`mamba` is needed to run the pipeline. It is a faster version of `conda`. `mamba` can be installed via `conda`. 

To install both, see the [conda/mamba Notion docs](https://www.notion.so/arcinstitute/Conda-Mamba-8106bed9553d46cca1af4e10f486bec2).

## Nextflow install

It is easiest to install Nextflow using `mamba`:

```bash
mamba install -n nextflow_env -c bioconda nextflow
```

## Pipeline install

```bash
git clone https://github.com/ArcInstitute/Lizard-Wizard \
  && cd Lizard-Wizard
```

### Pipeline conda environments 

The pipeline uses conda environment to manage dependencies. 
Nextflow will automatically create the environments as long as `mamba` is installed.
**Note:** it can take a while to create the environments, even with `mamba`.


# Usage

## Parameters 

See `nextflow.config` for the parameters that can be set.

## Example Run

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -process.scratch /media/8TBNVME/multiomics/ \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)/lizard-wizard
  --input /path/to/image/files/ \
  --output /path/to/output/location/
```

**Notes:**

* See `./nextflow.config` for all input parameters (e.g., specifying the input file type).
* If you are not in the `multiomics` user group (check by running the `groups` command), 
  you will need to change the `scratch` and `work-dir` paths.

## Test runs

Below are test runs with sample datasets.

### Local runs 

> `Local` means using the resources in your current session, instead of submitting jobs to the cluster.
>  Note: you might need to increase the number of CPUs and memory in order to run the pipeline locally.

Zeiss 3d:

```bash
nextflow run main.nf \
  -profile dev_zeiss_3d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)/lizard-wizard
```

Molecular devices 3d:

```bash
nextflow run main.nf \
  -profile dev_moldev_3d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)/lizard-wizard
```

Molecular devices 2d:

```bash
nextflow run main.nf \
  -profile dev_moldev_2d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)/lizard-wizard
```

### Slurm runs

An example of processing Zeiss 3d images on the cluster:

```bash
nextflow run main.nf \
  -profile dev_zeiss_3d,conda,slurm \
  -process.scratch /media/8TBNVME/multiomics/ \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)
```

# Resources

* [calcium_image_analysis codebase](https://github.com/ArcInstitute/calcium_image_analysis)
* [workflow diagram on Miro](https://miro.com/welcomeonboard/SVJGR3Z3QzVqYUFrdWN4RWxqTG9kYXd5d0UwcDZBdXlOMzVlO[…]1RU4wanwzNDU4NzY0NTkzMTk5MTQwMzg4fDI=?share_link_id=667093308277)

# Workflow

## Input

* Params
  * Directory of images (`*.czi` files)
  * Output directory

## Processing

* Create sample sheet
  * Format: 
    * `file_basename,file_path`
  * Python script to create csv file of images
    * If `zeiss`: 
      * `get_czi_files`
        * lists `*.csz` files
    * If `moldev`: 
      * `concatenate_moldev_files`
        * Concatenates related TIFF files; groups by 
* Load sample sheet as channel
* If `spot_check > 0`, randomly subsample images
* For each image:
  * run `zeiss_caiman_process` 
    * mask each image
      * cellpose detection
    * run `caiman` on each image
      * [setup_cluster() info](https://github.com/flatironinstitute/CaImAn/blob/e7e86411e80639c81d8ea58026660913739704f7/docs/source/Getting_Started.rst#cluster-setup-and-shutdown)
  
***

# Dev

## TODO

[ ] Add metrics
[ ] Fix `calc_dff_f0`
[ ] Add log summary
[ ] Update Caiman (stop using github release)

## Local runs

Zeiss 3d:

```bash
nextflow run main.nf \
  -profile dev_zeiss_3d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)/lizard-wizard
```

Molecular devices 3d:

```bash
nextflow run main.nf \
  -profile dev_moldev_3d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)/lizard-wizard
```

Molecular devices 2d:

```bash
nextflow run main.nf \
  -profile dev_moldev_2d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)/lizard-wizard
```

## Slurm runs

```bash
nextflow run main.nf \
  --test_image_count 3 \
  -profile dev_zeiss_3d,conda,slurm \
  -process.scratch /media/8TBNVME/multiomics/ \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)/lizard-wizard
```

## Data 

### local

`/large_experiments/multiomics/lizard_wizard`

### GCP

* Zeiss - 3d
  * VM: `caiman-cmtc-vm`
    * `/home/sneha.rao/vm_directory/GCP/2024-04-17/`
* Molecular devices - 2d
  * VM: `caiman-cmtc-vm`
    * `/home/sneha.rao/vm_directory/Jay/`
* Molecular devices - 3d
  * NAS
    * `/Volumes/ARC-DATA/LabDevices/220-4-ML/MD ImageXpress/CMTC/Sneha/Calcium_AAV-GCAMP_6wk_20240416`

