Lizard Wizard
=============

<img src="./img/lizard-wizard.png" alt="drawing" width="400"/>

Calcium imaging analysis Nextflow pipeline for the Arc Institute.

# Dev

## TODO

[ ] Update Caiman (stop using github release)

## Local runs

Zeiss 3d:

```bash
nextflow run main.nf \
  -profile dev_zeiss_3d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)
```

Molecular devices 3d:

```bash
nextflow run main.nf \
  -profile dev_moldev_3d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)
```

Molecular devices 2d:

```bash
nextflow run main.nf \
  -profile dev_moldev_2d,vm,conda \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)
```

## Slurm runs

```bash
nextflow run main.nf \
  -profile dev_zeiss_3d,conda,slurm \
  -process.scratch /media/8TBNVME/multiomics/ \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)
```

# Installation

## Conda & mamba install

`mamba` is needed to run the pipeline. It is a faster version of `conda`. `mamba` can be installed via `conda`. 

To install both, see the [conda/mamba Notion docs](https://www.notion.so/arcinstitute/Conda-Mamba-8106bed9553d46cca1af4e10f486bec2).

## Nextflow install

It is easiest to install Nextflow using `mamba`:

```bash
mamba install -n nextflow_env -c bioconda nextflow
```

## Pipeline conda environments 

The pipeline uses conda environment to manage dependencies. 
Nextflow will automatically create the environments as long as `mamba` is installed.
**Note:** it can take a while to create the environments, even with `mamba`.

## Parameters 

See `nextflow.config` for the parameters that can be set.

## Run

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -process.scratch /media/8TBNVME/multiomics/ \
  -work-dir /checkpoint/multiomics/nextflow-work/$(whoami)
  --input 
```

> If you are not in the `multiomics` user group (check by running the `groups` command), 
> you will need to change the `scratch` and `work-dir` paths.


# Usage

**TODO**

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
  

# Data 

## local

`/large_experiments/multiomics/lizard_wizard`

## GCP

* Zeiss - 3d
  * VM: `caiman-cmtc-vm`
    * `/home/sneha.rao/vm_directory/GCP/2024-04-17/`
* Molecular devices - 2d
  * VM: `caiman-cmtc-vm`
    * `/home/sneha.rao/vm_directory/Jay/`
* Molecular devices - 3d
  * NAS
    * `/Volumes/ARC-DATA/LabDevices/220-4-ML/MD ImageXpress/CMTC/Sneha/Calcium_AAV-GCAMP_6wk_20240416`

