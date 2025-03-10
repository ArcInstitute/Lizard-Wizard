Lizard Wizard
=============

<img src="./img/lizard-wizard.png" alt="drawing" width="400"/>

**Calcium Image Processing Nextflow pipeline for the Arc Institute.**

The Lizard Wizard pipeline helps researchers analyze subcellular Ca²⁺ signals captured using fluorescent Ca²⁺ indicators. This pipeline automates the detection and analysis of calcium signals, simplifying complex image processing tasks and providing detailed metrics for understanding neural activity.

**Table of Contents**

- [Lizard Wizard](#lizard-wizard)
  - [Overview](#overview)
  - [Features](#features)
- [Installation](#installation)
  - [Conda \& mamba install](#conda--mamba-install)
  - [Nextflow install](#nextflow-install)
  - [Pipeline install](#pipeline-install)
    - [Add ssh key to GitHub](#add-ssh-key-to-github)
    - [Clone the Repository](#clone-the-repository)
    - [Pipeline conda environments](#pipeline-conda-environments)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Example Run](#example-run)
  - [Parameters](#parameters)
  - [Tutorials](#tutorials)
  - [Secrets](#secrets)
- [Resources](#resources)
  - [Output Files](#output-files)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Overview

Calcium imaging is a powerful technique for monitoring cellular activity, but processing and analyzing this data involves multiple complex steps. Lizard Wizard automates this entire process for biologists, from input image preprocessing to detailed neuron-level analysis, integrating:

- [CaImAn](https://github.com/flatironinstitute/CaImAn) for calcium event detection
- [Cellpose](https://github.com/MouseLand/cellpose) for cell segmentation
- [Wizards-Staff](https://github.com/ArcInstitute/Wizards-Staff) for pairwise correlations, synchronicity analysis, and more

This integrated approach makes calcium imaging analysis more accessible, reproducible, and efficient.

## Features

- **Comprehensive Pipeline**: Processes raw calcium imaging data from multiple microscope types (Molecular Devices, Zeiss) through a complete analysis workflow
- **Automated Masking**: Uses Cellpose for precise identification of regions of interest (ROIs)
- **Calcium Event Analysis**: Leverages CaImAn for automated extraction of neuronal activity
- **Detailed Metrics Calculation**: performed via automated Wizard's Staff Integration.

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

### Clone the Repository

```bash
git clone git@github.com:ArcInstitute/Lizard-Wizard.git \
  && cd Lizard-Wizard
```

### Pipeline conda environments 

The first time you run the pipeline, Nextflow will automatically create all necessary conda environments. This process may take some time but only happens once.

**Note:** it can take a while to create the environments, even with `mamba`.


# Usage

## Quick Start

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
  --input_dir /path/to/your/images/ \
  --output_dir /path/to/output/location/ \
  --test_image_count 2 \
  -N your.email@example.com
```
## Example Run

We recommend a two-step approach:

1. **Spot Check**: Run the pipeline on a few images first to verify parameters. This will run Lizard Wizard utilizing preset parameters, we recommend reading through the general [Tutorial](docs/lizardwizard_tutorial.md) for detailed information on how to adjust parameters to your dataset during this step.

   ```bash
   nextflow run main.nf \
     -profile conda,slurm \
     -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
     --input_dir /path/to/image/files/ \
     --output_dir /path/to/output/location/ \
     --test_image_count 3 \
     -N your.email@example.com
   ```

2. **Full Run**: Process the entire dataset using the same output directory

   ```bash
   nextflow run main.nf \
     -profile conda,slurm \
     -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
     --input_dir /path/to/image/files/ \
     --output_dir /path/to/output/location/ \
     -N your.email@example.com \
     -resume
   ```

## Parameters 

The pipeline has many configurable parameters that can be set via command line or config files. See either `nextflow.config` or the general [Tutorial](docs/lizardwizard_tutorial.md) for detailed information about setting these parameters for your specific data type.

Key parameters include:

- `--input_dir`: Path to input images
- `--output_dir`: Where to save results
- `--file_type`: Set to "moldev" or "zeiss" depending on your microscope
- `--use_2d`: Set to `true` for 2D images instead of 3D (default: `false`)
- `--test_image_count`: Number of random images to process for testing
- `--test_image_names`: Specify particular images to process (comma-separated)

## Tutorials

For detailed guidance on how to use Lizard Wizard and the accompanying Wizards Staff with your data, see:

- [Lizard Wizard Tutorial](docs/lizardwizard_tutorial.md) - How to configure parameters for Lizard Wizard and account for different data types
- [Output Files Guide](docs/output_files.md) - Understanding the outputs of the Lizard Wizard pipeline
- [Troubleshooting Guide](docs/troubleshooting.md) - Common issues and solutions
  
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

# Resources

* [calcium_image_analysis codebase](https://github.com/ArcInstitute/calcium_image_analysis)
* [workflow diagram on Miro](https://miro.com/welcomeonboard/SVJGR3Z3QzVqYUFrdWN4RWxqTG9kYXd5d0UwcDZBdXlOMzVlO[…]1RU4wanwzNDU4NzY0NTkzMTk5MTQwMzg4fDI=?share_link_id=667093308277)

## Output Files

The pipeline produces a structured output directory containing:

- Processed images
- Neuronal activity data
- Metrics tables
- Visualization plots
- Log summaries

See the [Output Files Guide](./docs/output_files.md) for detailed information.

## License

This project is licensed under the [MIT License](./LICENSE) - see the LICENSE file for details.

## Acknowledgments

- [CaImAn](https://github.com/flatironinstitute/CaImAn) for calcium imaging analysis
- [Cellpose](https://github.com/MouseLand/cellpose) for cell segmentation
- [Nextflow](https://www.nextflow.io/) for workflow management
- The Arc Institute for supporting this research