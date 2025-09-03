Lizard Wizard
=============

<img src="./img/lizard-wizard.png" alt="drawing" width="400"/>

**Calcium Image Processing Nextflow pipeline for the Arc Institute.**

Lizard Wizard automates detection, segmentation, and analysis of calcium signals from 2D/3D fluorescence imaging. It integrates CaImAn, Cellpose, and Wizards Staff to produce high-quality metrics and visualizations for downstream analysis.

## Table of Contents

- [Lizard Wizard](#lizard-wizard)
  - [Table of Contents](#table-of-contents)
  - [What is Lizard Wizard?](#what-is-lizard-wizard)
  - [Key Features](#key-features)
  - [Workflow Diagram](#workflow-diagram)
  - [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Conda \& mamba install](#conda--mamba-install)
  - [Nextflow install](#nextflow-install)
  - [Pipeline install](#pipeline-install)
    - [Clone the Repository](#clone-the-repository)
    - [Cloning the Repo: SSH vs HTTPS (and fixing publickey errors)](#cloning-the-repo-ssh-vs-https-and-fixing-publickey-errors)
    - [Two ways to clone](#two-ways-to-clone)
    - [If you see: Permission denied (publickey)](#if-you-see-permission-denied-publickey)
    - [Pipeline conda environments](#pipeline-conda-environments)
    - [Singularity](#singularity)
  - [Usage](#usage)
    - [Example Run](#example-run)
    - [Running with Singularity (Chimera cluster)](#running-with-singularity-chimera-cluster)
      - [Prerequisites](#prerequisites)
      - [Container Locations](#container-locations)
      - [Profiles Overview](#profiles-overview)
      - [Required Params for Chimera](#required-params-for-chimera)
      - [Minimal Run Examples](#minimal-run-examples)
      - [Outputs, Trace \& Reports](#outputs-trace--reports)
    - [Parameters](#parameters)
  - [Wizards Staff Integration](#wizards-staff-integration)
  - [Tutorials and Guides](#tutorials-and-guides)
  - [Best Practices](#best-practices)
  - [Advanced Usage](#advanced-usage)
  - [Secrets](#secrets)
  - [Quick Troubleshooting](#quick-troubleshooting)
  - [Output Files](#output-files)
  - [Citation](#citation)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## What is Lizard Wizard?

Lizard Wizard is a reproducible Nextflow pipeline that takes raw time-lapse fluorescence imaging and returns curated calcium activity traces, ROIs, QC plots, and advanced metrics. It integrates:

- [CaImAn](https://github.com/flatironinstitute/CaImAn) for calcium event extraction
- [Cellpose](https://github.com/MouseLand/cellpose) for segmentation/masking
- [Wizards-Staff](https://github.com/ArcInstitute/Wizards-Staff) for clustering, correlations, and summary metrics

This integrated approach is designed for biologists who need robust analysis without writing custom code for every dataset.

## Key Features

- **End-to-end workflow**: Ingest → Mask → CaImAn → ΔF/F₀ → Metrics → Reports
- **CaImAn-based extraction**: Spatial footprints, temporal traces, and denoised activity
- **Cellpose segmentation**: Reliable ROIs for 2D cultures and 3D organoids
- **Wizards Staff metrics**: Clustering, pairwise correlations, FRPM, rise time, FWHM
- **Reproducible by design**: Nextflow + Conda/Singularity for portable, pinned environments
- **HPC-ready**: SLURM-friendly profiles and scratch work directories
- **Interoperable outputs**: NPY/CSV/PNG organized for downstream analysis

## Workflow Diagram

```mermaid
flowchart LR
  A[Raw images (Zeiss/MolDev)] --> B[Masking (Cellpose)]
  B --> C[CaImAn extraction]
  C --> D[ΔF/F₀ normalization]
  D --> E[Wizards Staff metrics]
  E --> F[Reports, plots, CSV, NPY]
```

## Quick Start

Run a spot check on a few images (recommended):

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
  --input_dir /path/to/images/ \
  --output_dir /path/to/output/ \
  --test_image_count 2 \
  -N your.email@example.com
```

Then process the full dataset, reusing results:

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
  --input_dir /path/to/images/ \
  --output_dir /path/to/output/ \
  -N your.email@example.com \
  -resume
```

Expected outputs are written to `--output_dir` (see [Output Files Guide](./docs/output_files.md)).

## Installation

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

### Clone the Repository

```bash
git clone git@github.com:ArcInstitute/Lizard-Wizard.git \
  && cd Lizard-Wizard
```

### Cloning the Repo: SSH vs HTTPS (and fixing publickey errors)

### Two ways to clone

HTTPS (simplest, no SSH keys needed):
```bash
git clone https://github.com/ArcInstitute/Lizard-Wizard.git
cd Lizard-Wizard
```

SSH (requires GitHub auth/key):
```bash
git clone git@github.com:ArcInstitute/Lizard-Wizard.git
cd Lizard-Wizard
```

### If you see: Permission denied (publickey)

Option 1: Switch to HTTPS:
```bash
git clone https://github.com/ArcInstitute/Lizard-Wizard.git
```

Option 2: Set up GitHub CLI and authenticate (works well on HPC nodes):
```bash
conda install -c conda-forge gh
gh auth login
```
Follow the prompts to authenticate with your GitHub account (HTTPS or SSH).

Test your SSH:
```bash
ssh -T git@github.com
```

Retry the clone:
```bash
git clone git@github.com:ArcInstitute/Lizard-Wizard.git
```

Note for internal users:

- If your organization restricts outbound SSH, prefer the HTTPS clone method.
- Ensure your `$HOME/.ssh` and `$HOME/.config` are writable or use HTTPS + `gh` token auth.

### Pipeline conda environments

The first time you run the pipeline, Nextflow will automatically create all necessary conda environments.
This process may take some time but only happens once.

**Note:** it can take a while to create the environments, even with `mamba`.

### Singularity

For reproducible runs on Arc Internal Cluster, use Singularity containers built from the `singularity/*.def` files.

Build all containers and validate:

```bash
./build_singularity_containers.sh
./validate_singularity_setup.sh
```

Run the pipeline with Singularity profiles:

```bash
nextflow run main.nf \
  -profile singularity,chimera,slurm \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
  --input_dir /path/to/your/images/ \
  --output_dir /path/to/output/location/ \
  --test_image_count 2
```


## Usage

### Example Run

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

   > Update `-work-dir` as needed for your file system

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

   > Update `-work-dir` as needed for your file system

### Running with Singularity (Chimera cluster)

#### Prerequisites
- **Nextflow**: >= 24.10.0 recommended
- **Singularity or Apptainer**
- **SLURM access on Chimera**
- **Access to shared container directory**: `/large_storage/multiomics/public/singularity/lizard-wizard`

#### Container Locations

```text
/large_storage/multiomics/public/singularity/lizard-wizard/
  ├─ caiman.sif
  ├─ cellpose.sif
  ├─ summary.sif
  └─ wizards_staff.sif
```

#### Profiles Overview
- **-profile singularity**: enables containers and maps process labels to the above `.sif` paths via `params.singularity_path`.
- **-profile chimera_singularity**: convenience profile combining Singularity + Chimera site defaults (if configured).
- You can override the container root with `--singularity_path` if containers live elsewhere.

#### Required Params for Chimera
- Set the Singularity path if not defined in configs:
  - `--singularity_path /large_storage/multiomics/public/singularity/lizard-wizard`
- Recommended scratch work dir:
  - `-work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard`

#### Minimal Run Examples

Option A: Use the generic Singularity profile

```bash
nextflow run main.nf \
  -profile singularity \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
  --singularity_path /large_storage/multiomics/public/singularity/lizard-wizard \
  --input_dir /path/to/your/data/ \
  --output_dir /path/to/save/data/to/ \
  --file_type moldev \
  etc...
```

Add `-resume` to reuse completed tasks:

```bash
... -resume
```

#### Outputs, Trace & Reports
- Use `--output_dir` for results.
- If enabled, reports and traces are written to `${output_dir}/nf-report/` and `${output_dir}/nf-trace/`.

### Parameters

The pipeline has many configurable parameters that can be set via command line or config files. See either `nextflow.config` or the general [Tutorial](docs/lizardwizard_tutorial.md) for detailed information about setting these parameters for your specific data type.

Key parameters include:

- `--input_dir`: Path to input images
- `--output_dir`: Where to save results
- `--file_type`: Set to "moldev" or "zeiss" depending on your microscope
- `--use_2d`: Set to `true` for 2D images instead of 3D (default: `false`)
- `--test_image_count`: Number of random images to process for testing
- `--test_image_names`: Specify particular images to process (comma-separated)

For parameter selection strategies and recommended starting values by data type, see the [Tutorial](./docs/lizardwizard_tutorial.md#key-parameters-overview).

## Wizards Staff Integration

Outputs from CaImAn and ΔF/F₀ data are automatically passed to [Wizards Staff](https://github.com/ArcInstitute/Wizards-Staff) to compute clustering, correlations, firing rate per minute, rise time, FWHM, and additional QC plots. You can find these results under `wizards-staff/` in your `--output_dir`. See the [Output Files Guide](./docs/output_files.md#wizards-staff-outputs) for details and the [Tutorial](./docs/lizardwizard_tutorial.md) for how to tune inputs that affect downstream metrics.

## Tutorials and Guides

For detailed guidance on how to use Lizard Wizard and the accompanying Wizards Staff with your data, see:

- [Lizard Wizard Tutorial](./docs/lizardwizard_tutorial.md) — Parameter selection, datasets, and workflows
- [Output Files Guide](./docs/output_files.md) — What each file means and how to use it
- [Troubleshooting Guide](./docs/troubleshooting.md) — Common issues and diagnostic commands

## Best Practices

- Organize data per experiment with clear folder names and metadata (`metadata.csv` produced in outputs can be extended).
- Start with a spot check (`--test_image_count`) to tune `--gSig`, `--min_corr`, `--min_pnr`.
- Use a scratch `-work-dir` on fast storage; add `-resume` for iterative runs.
- Record the exact command and Nextflow version used for each production run.

## Advanced Usage

- Batch processing: submit multiple Nextflow runs by condition, pointing to the same `-work-dir` and distinct `--output_dir` per condition.
- Custom parameters: use a Nextflow `-params-file params.json` to store a reusable configuration.
- Profiles: create site- or lab-specific profiles in `nextflow.config` for CPUs, memory, and container paths.
  
## Secrets

**[Optional]** The pipeline uses gpt-4o(-mini) to summarize the log files.
This optional feature requires an `OPENAI_API_KEY` to be set as a Nextflow secret.
To set the secret (assuming that `OPENAI_API_KEY` is set in the environment):

```bash
nextflow secrets set OPENAI_API_KEY $OPENAI_API_KEY
```

**Notes:**
* If you do not set `OPENAI_API_KEY`, then the log summaries will be blank.

## Quick Troubleshooting

- Nextflow not found: ensure you activated the env (`conda activate nextflow_env`).
- Pipeline stalls/fails: check `.nextflow.log` and `logs/` under `--output_dir`, then re-run with `-resume`.
- No neurons detected: lower `--min_corr`/`--min_pnr`, verify `--gSig` and masking outputs.
- See the full [Troubleshooting Guide](./docs/troubleshooting.md) for more.

## Output Files

See the [Output Files Guide](./docs/output_files.md) for structure, examples, and how to load data in Python/R.

## Citation

If you use Lizard Wizard in your research, please cite the repository and the underlying tools:

- Lizard Wizard (this repository)
- CaImAn: Giovannucci et al., eLife (2019)
- Cellpose: Stringer et al., Nat Methods (2021)
- Wizards Staff ([Repo](https://github.com/ArcInstitute/Wizards-Staff), Arc Institute)

## License

This project is licensed under the [MIT License](./LICENSE) - see the LICENSE file for details.

## Acknowledgments

- [CaImAn](https://github.com/flatironinstitute/CaImAn) for calcium imaging analysis
- [Cellpose](https://github.com/MouseLand/cellpose) for cell segmentation
- [Nextflow](https://www.nextflow.io/) for workflow management
- [Arc Institute](https://www.arcinstitute.org/) for supporting this research