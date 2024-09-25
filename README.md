Lizard Wizard
=============

<img src="./img/lizard-wizard.png" alt="drawing" width="400"/>

**Calcium Image Processing Nextflow pipeline for the Arc Institute.**

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

To install both `conda` and `mamba`, see the [conda/mamba Notion docs](https://www.notion.so/arcinstitute/Conda-Mamba-8106bed9553d46cca1af4e10f486bec2).

## Nextflow install

It is easiest to install Nextflow using `mamba`:

```bash
mamba install -n nextflow_env -c bioconda nextflow
```

Make sure to activate the environment before running the pipeline:

```bash
mamba activate nextflow_env
```

## Pipeline install

### Add ssh key to GitHub

> This is only needed if you have not already added your ssh key to GitHub.

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

* change `your_email@example.com` to your Arc email

```bash
cat ~/.ssh/id_ed25519.pub
```

* copy the output
* GoTo: `GitHub => Settings > SSH and GPG keys > New SSH key`
* Paste the output into the key field
* Add a title (e.g., `Chimera`)
* Click `Add SSH key`

### Clone the repo

```bash
git clone git@github.com:ArcInstitute/Lizard-Wizard.git \
  && cd Lizard-Wizard
```

### Pipeline conda environments 

The pipeline uses conda environments to manage dependencies. 
Nextflow will automatically create the environments as long as `mamba` is installed.

**Note:** it can take a while to create the environments, even with `mamba`.


# Usage

## Parameters 

See `nextflow.config` for the parameters that can be set.

## Secrets

**[Optional]** The pipeline uses gpt-4o(-mini) to summarize the log files.
This optional feature requires an `OPENAI_API_KEY` to be set as a Nextflow secret.
To set the secret (assuming that `OPENAI_API_KEY` is set in the environment):

```bash
nextflow secrets set OPENAI_API_KEY $OPENAI_API_KEY
```

**Notes:**
* If you do not set `OPENAI_API_KEY`, then the log summaries will be blank.
* Ask Nick for the `OPENAI_API_KEY` value.

## Example Spot-Check Run

A spot check is a small run of the pipeline to ensure that the pipeline parameters are set correctly.

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
  --input_dir /path/to/image/files/ \
  --output_dir /path/to/output/location/ \
  --test_image_count 3 \
  -N YOUR_EMAIL_HERE@arcinstitute.org
```

**Notes:**

* Replace `YOUR_EMAIL_HERE@arcinstitute.org` with your email.
  * It is used to send the pipeline status updates (e.g., error and completion messages).
  * You do not have to use `-N`, but it is recommended.
* `--test_image_count 3` will run the pipeline on 3 randomly selected images.
  * You can also select specific images by using `--test_image_names` 
    * e.g., `--test_image_names 10xGCaMP-6wk-F08_s1_FITC,10xGCaMP-6wk-D10_s1_FITC`.
* See `./nextflow.config` for all input parameters (e.g., specifying the input file type).
* **Make sure** to change the `--input_dir` and `--output_dir` paths to the correct locations.
* Use `--file_type zeiss` if the input files are from the Zeiss microscope.
* If the data is 2d instead of 3d (default), use `--use_2d true`.

## Example Full Run

After running the spot check, you can process the full dataset.

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
  --input_dir /path/to/image/files/ \
  --output_dir /path/to/output/location/ \
  -N YOUR_EMAIL_HERE@arcinstitute.org \
  -resume
```

**Notes:**
* Be sure to replace `YOUR_EMAIL_HERE@arcinstitute.org` with your email.
* The `-resume` flag will prevent the need to re-run the samples included in the spot check, 
  since they are already processed.
  * For this to work, the `--output_dir` directory must be the same as the spot check run.
* **Make sure** to change the `--input_dir` and `--output_dir` paths to the correct locations.


## Test runs

Below are test runs with sample datasets.

### Local runs 

> `Local` means using the resources in your current session, instead of submitting jobs to the cluster.
>  Note: you might need to increase the number of CPUs and memory in order to run the pipeline locally.

Zeiss 3d:

```bash
nextflow run main.nf \
  -profile dev_zeiss_3d,vm,conda \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard
```

Molecular Devices 3d:

```bash
nextflow run main.nf \
  -profile dev_moldev_3d,vm,conda \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard
```

Molecular Devices 2d:

```bash
nextflow run main.nf \
  -profile dev_moldev_2d,vm,conda \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard
```

Simulated Molecular Devices 2d:

```bash
nextflow run main.nf \
  -profile dev_moldev_2d_sim,vm,conda \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard
```

### Slurm runs

An example of processing Zeiss 3d images on the cluster:

```bash
nextflow run main.nf \
  -profile dev_zeiss_3d,conda,slurm \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard
```

# Resources

* [calcium_image_analysis codebase](https://github.com/ArcInstitute/calcium_image_analysis)
* [workflow diagram on Miro](https://miro.com/welcomeonboard/SVJGR3Z3QzVqYUFrdWN4RWxqTG9kYXd5d0UwcDZBdXlOMzVlO[…]1RU4wanwzNDU4NzY0NTkzMTk5MTQwMzg4fDI=?share_link_id=667093308277)

# Workflow

## Input

* Directory of images 
* Nextflow parameters (`nextflow.config` file)

## Processing

* Format input
  * If `moldev`, concatenate files
  * If `zeiss`, load images
* For each image:
  * Mask via Cellpose
  * Run CaImAn
  * Calc F/F0 on CaImAn output
  * Summarize the logs (optional)

## Output

* Processed images and other files
* Written to the `--output_dir` directory

***

# Dev

## Local runs

Zeiss 3d:

```bash
nextflow run main.nf -profile dev_zeiss_3d,vm,conda 
```

Molecular devices 3d:

```bash
nextflow run main.nf -profile dev_moldev_3d,vm,conda
```

Molecular devices 2d:

```bash
nextflow run main.nf -profile dev_moldev_2d,vm,conda
```

## Slurm runs

```bash
nextflow run main.nf \
  -profile dev_zeiss_3d,conda,slurm \
  --test_image_count 3
```

```bash
nextflow run main.nf \
  -profile dev_moldev_3d,conda,slurm \
  --test_image_count 3
```

```bash
nextflow run main.nf \
  -profile dev_moldev_2d,conda,slurm \
  --test_image_count 3
```

## Data 

### local

`/large_storage/multiomics/lizard_wizard`

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

