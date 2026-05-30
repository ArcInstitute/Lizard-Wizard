Lizard Wizard
=============

<img src="./img/lizard-wizard.png" alt="drawing" width="400"/>

**Calcium image processing Nextflow pipeline, developed at the Arc Institute.**

Lizard Wizard automates detection, segmentation, and analysis of calcium signals from 2D/3D fluorescence imaging. It integrates CaImAn, Cellpose, and Wizards Staff to produce high-quality metrics and visualizations for downstream analysis.

> **New here? You do not need to be at the Arc Institute to use Lizard Wizard.**
> It runs on a laptop/lab server, an institutional HPC (SLURM), or the cloud (AWS/GCP).
> Start with the [Choose Your Environment](#choose-your-environment) section, then the [Quick Start](#quick-start).
> Arc-internal instructions (the "Chimera" cluster) are clearly labeled **[Arc internal]** and are optional for everyone else.

## Table of Contents

- [Lizard Wizard](#lizard-wizard)
  - [Table of Contents](#table-of-contents)
  - [What is Lizard Wizard?](#what-is-lizard-wizard)
  - [Key Features](#key-features)
  - [Workflow Diagram](#workflow-diagram)
  - [Choose Your Environment](#choose-your-environment)
  - [Quick Start](#quick-start)
  - [Installation](#installation)
    - [Install conda \& mamba](#install-conda--mamba)
    - [Install Nextflow](#install-nextflow)
    - [Get the pipeline](#get-the-pipeline)
      - [Cloning the repo: SSH vs HTTPS (and fixing publickey errors)](#cloning-the-repo-ssh-vs-https-and-fixing-publickey-errors)
  - [Software Environments (containers vs conda)](#software-environments-containers-vs-conda)
    - [Option 1: Conda / mamba (no containers)](#option-1-conda--mamba-no-containers)
    - [Option 2: Docker](#option-2-docker)
    - [Option 3: Singularity / Apptainer (build your own containers)](#option-3-singularity--apptainer-build-your-own-containers)
  - [Running Lizard Wizard](#running-lizard-wizard)
    - [Local / single machine](#local--single-machine)
    - [Generic HPC (SLURM)](#generic-hpc-slurm)
    - [AWS Batch](#aws-batch)
    - [GCP Batch](#gcp-batch)
    - [Running on Arc's Chimera cluster (internal)](#running-on-arcs-chimera-cluster-internal)
  - [Usage](#usage)
    - [Recommended two-step run](#recommended-two-step-run)
    - [Parameters](#parameters)
  - [Wizards Staff Integration](#wizards-staff-integration)
  - [Tutorials and Guides](#tutorials-and-guides)
  - [Best Practices](#best-practices)
  - [Advanced Usage](#advanced-usage)
  - [Secrets (optional OpenAI integration)](#secrets-optional-openai-integration)
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
- **Reproducible by design**: Nextflow + Conda/Docker/Singularity for portable, pinned environments
- **Runs anywhere**: laptop/lab server, institutional HPC (SLURM), or cloud (AWS/GCP)
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

## Choose Your Environment

Lizard Wizard is configured with Nextflow **profiles**. You combine a *container/conda* profile with an *executor* profile, e.g. `-profile conda` (local) or `-profile conda,slurm_generic` (HPC). Pick the row that matches where you want to run:

| Where you run | Recommended `-profile` | Scheduler | Environments | Notes |
|---|---|---|---|---|
| **Local** laptop / lab server | `conda` | none (local) | conda (auto-built) | Easiest way to start. Works with the built-in simulated dataset — no external data needed. |
| **Institutional HPC** (SLURM) | `conda,slurm_generic` *(or)* `singularity,slurm_generic` | SLURM | conda *(or)* your own `.sif` | Override the partition/queue and resource caps for your site (see [Generic HPC](#generic-hpc-slurm)). |
| **AWS** | `awsbatch` | AWS Batch | container image (you supply) | Requires an AWS Batch compute environment + S3 work bucket + container images (see [AWS Batch](#aws-batch)). |
| **GCP** | `gcp` | Google Batch | container image (you supply) | Requires a GCP project + GCS work bucket + container images (see [GCP Batch](#gcp-batch)). |
| **Arc Chimera** *(internal)* | `conda,chimera,slurm` *(or)* `singularity,chimera_singularity,slurm` | SLURM | conda *(or)* shared `.sif` | **[Arc internal]** only — depends on Arc paths. See [Arc's Chimera cluster](#running-on-arcs-chimera-cluster-internal). |

Profile cheat-sheet:

- **Environments (pick one):** `conda` (auto-built, most portable), `singularity` (build your own `.sif`), or `docker` (you supply images — see [Docker](#option-2-docker)).
- **Executor (pick one):** *(omit for local)*, `slurm_generic`, `awsbatch`, `gcp`. Arc-internal: `slurm` (Chimera-tuned), `chimera`, `chimera_singularity`.
- **Optional add-ons:** `report` (HTML run report), `trace` (per-task trace file).

> **Heads-up on containers:** Lizard Wizard does **not** publish prebuilt Docker/Singularity images to any public registry. The `conda` profile needs nothing extra. The `singularity` profile requires you to build `.sif` files once (see [Option 3](#option-3-singularity--apptainer-build-your-own-containers)). The cloud profiles (`awsbatch`, `gcp`) run jobs in containers, so you must build images and push them to a registry your cloud can pull from, or adapt the profiles to your own images.

You can list every profile in [`config/profiles.config`](./config/profiles.config).

## Quick Start

The fastest way to see the pipeline run end-to-end — **no microscope data and no HPC required**. This uses the bundled synthetic dataset (`data/synthetic_puffs_movie.tiff`) and conda on your local machine. The `conda` profile is the most portable starting point because Nextflow builds the required environments for you (no container images to fetch or build):

```bash
# 1) Clone
git clone https://github.com/ArcInstitute/Lizard-Wizard.git
cd Lizard-Wizard

# 2) Install Nextflow (see Installation if you don't have conda/mamba yet)
mamba create -n nextflow_env -c bioconda nextflow -y
mamba activate nextflow_env

# 3) Run on simulated data (the first run builds the conda environments automatically)
nextflow run main.nf \
  -profile conda \
  --simulate true \
  --num_simulations 2 \
  --output_dir ./results_sim/
```

Once that works, point the pipeline at your own images:

```bash
nextflow run main.nf \
  -profile conda \
  --input_dir /path/to/images/ \
  --output_dir ./results/ \
  --file_type moldev \
  --test_image_count 2
```

Prefer containers? See [Software Environments](#software-environments-containers-vs-conda) for Singularity/Apptainer (build your own `.sif`) and Docker. Outputs are written to `--output_dir` (see the [Output Files Guide](./docs/output_files.md)). To scale up to a cluster or cloud, see [Running Lizard Wizard](#running-lizard-wizard).

## Installation

You need three things: **conda/mamba**, **Nextflow**, and a **container engine** (Docker or Singularity) *or* nothing extra if you use the `conda` profile.

### Install conda & mamba

`mamba` is a faster drop-in replacement for `conda` and is recommended for creating environments. The easiest way to get both is **Miniforge**, which ships `conda` + `mamba` together:

- **Miniforge (recommended):** <https://github.com/conda-forge/miniforge#install>
- Miniconda: <https://docs.anaconda.com/miniconda/>
- Mamba docs: <https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html>

After installing, restart your shell and confirm:

```bash
conda --version
mamba --version
```

### Install Nextflow

Install Nextflow into its own environment with `mamba`:

```bash
mamba create -n nextflow_env -c bioconda nextflow -y
mamba activate nextflow_env
nextflow -version   # Nextflow >= 24.10.0 recommended; requires Java 17+
```

Activate `nextflow_env` before every run.

### Get the pipeline

```bash
git clone https://github.com/ArcInstitute/Lizard-Wizard.git
cd Lizard-Wizard
```

#### Cloning the repo: SSH vs HTTPS (and fixing publickey errors)

Two ways to clone:

HTTPS (simplest, no SSH keys needed):

```bash
git clone https://github.com/ArcInstitute/Lizard-Wizard.git
cd Lizard-Wizard
```

SSH (requires a GitHub SSH key):

```bash
git clone git@github.com:ArcInstitute/Lizard-Wizard.git
cd Lizard-Wizard
```

If you see `Permission denied (publickey)`:

Option 1 — switch to HTTPS:

```bash
git clone https://github.com/ArcInstitute/Lizard-Wizard.git
```

Option 2 — authenticate with the GitHub CLI (works well on HPC login nodes):

```bash
conda install -c conda-forge gh
gh auth login          # follow the prompts (HTTPS or SSH)
ssh -T git@github.com  # test SSH, if you chose SSH
git clone git@github.com:ArcInstitute/Lizard-Wizard.git
```

> If your institution restricts outbound SSH, use the HTTPS method.

## Software Environments (containers vs conda)

Lizard Wizard runs four tools (CaImAn, Cellpose, Wizards Staff, and a summary step), each in its own pinned environment defined under [`envs/`](./envs/). You choose **one** of three ways to provide those environments. There is no central container registry — you either let conda build the environments, or you build the container images yourself.

### Option 1: Conda / mamba (no containers)

The simplest option. The first time you run with `-profile conda`, Nextflow uses `mamba` to build all environments automatically. This happens once and is then cached.

```bash
nextflow run main.nf -profile conda --simulate true --output_dir ./results_sim/
```

> Building the conda environments can take a while (10–30+ min) even with `mamba`. Subsequent runs reuse the cache.

### Option 2: Docker

The `docker` profile in [`config/profiles.config`](./config/profiles.config) enables Docker and sets sensible run options (non-root user, `linux/amd64` platform), **but it does not map any image to the pipeline's processes** — Lizard Wizard does not publish prebuilt images to a public registry. So `-profile docker` on its own will not work until you supply images. You have two practical choices:

- **Easiest:** use `-profile conda` instead (no images needed), or `-profile singularity` after building `.sif` files.
- **Bring your own images:** build a Docker image per environment from the `envs/*.yml` files (the same recipes the `.def` files use), push them to a registry you control (GHCR/Docker Hub/Quay), then map them to the four process labels in a custom profile:

```groovy
// config/profiles.config — example, replace with your own image references
docker_custom {
    docker.enabled = true
    process {
        withLabel: caiman_env        { container = 'YOUR_REGISTRY/lizard-wizard-caiman:TAG' }        // replace with your own
        withLabel: cellpose_env      { container = 'YOUR_REGISTRY/lizard-wizard-cellpose:TAG' }      // replace with your own
        withLabel: summary_env       { container = 'YOUR_REGISTRY/lizard-wizard-summary:TAG' }        // replace with your own
        withLabel: wizards_staff_env { container = 'YOUR_REGISTRY/lizard-wizard-wizards-staff:TAG' }  // replace with your own
    }
}
```

Requires a working Docker install (<https://docs.docker.com/get-docker/>). See [Advanced Usage](#advanced-usage) for the label-to-process mapping pattern.

### Option 3: Singularity / Apptainer (build your own containers)

Recommended on HPC where Docker is unavailable. **We do not host the `.sif` files anywhere public** — you build them once from the definition files in [`singularity/`](./singularity/).

Build prerequisites:

- Apptainer (>= 1.1) or Singularity (>= 3.8)
- Network egress (the `.def` files bootstrap from `docker.io/mambaorg/micromamba` and install packages from `envs/*.yml`)
- ~10–20 GB free disk and ~15–40 min depending on network/CPU

Build all containers and validate them:

```bash
./build_singularity_containers.sh            # builds into ./singularity/
./validate_singularity_setup.sh              # checks each .sif runs
```

This produces:

```text
singularity/
  ├─ caiman.sif
  ├─ cellpose.sif
  ├─ summary.sif
  └─ wizards_staff.sif
```

Tell the pipeline where the `.sif` files live (defaults to `./singularity`):

```bash
# Either set an env var once:
export LZW_SINGULARITY_PATH="$PWD/singularity"

# ...or pass it per-run:
nextflow run main.nf -profile singularity \
  --singularity_path /path/to/your/containers \
  --simulate true --output_dir ./results_sim/
```

> The base images come from the public `mambaorg/micromamba` image on Docker Hub — there are **no Arc-internal base images or registries**. The only external dependency at build time is pulling `Wizards-Staff` from GitHub over HTTPS (see [`envs/wizards_staff.yml`](./envs/wizards_staff.yml)); if your build node has no GitHub access, see the [Troubleshooting Guide](./docs/troubleshooting.md#singularity-specific-issues).

## Running Lizard Wizard

All commands below assume you have a container/conda environment ready (see [Software Environments](#software-environments-containers-vs-conda)) and `nextflow_env` activated.

> **About `-work-dir`:** Nextflow stages intermediate files in a work directory (default `./work`). On shared clusters you usually want this on fast scratch storage. **Scratch layout varies by cluster** — replace `<your-scratch>` below with whatever your site provides (e.g. `$SCRATCH`, `/scratch/$USER`, `/tmp/$USER`). Ask your HPC admins if unsure.

### Local / single machine

No scheduler required, and with `-profile conda` no containers either. Great for development, small datasets, and the simulated dataset.

```bash
# Simulated data (no input images needed):
nextflow run main.nf \
  -profile conda \
  --simulate true \
  --num_simulations 2 \
  --output_dir ./results_sim/

# Your own images (reduce resource expectations on a workstation):
nextflow run main.nf \
  -profile conda \
  --input_dir /path/to/images/ \
  --output_dir ./results/ \
  --file_type moldev \
  --test_image_count 2 \
  --max_cpus 8 \
  --max_memory 32.GB
```

> Calcium extraction is memory-hungry on real data. On a laptop, keep `--test_image_count` small (1–2) and lower `--max_cpus`/`--max_memory` to fit your machine.

### Generic HPC (SLURM)

Use `slurm_generic`, which does **not** assume any particular partition name or node size. Override the queue and resource caps for your site:

```bash
nextflow run main.nf \
  -profile conda,slurm_generic \
  -work-dir <your-scratch>/nextflow-work/lizard-wizard \
  --input_dir /path/to/images/ \
  --output_dir /path/to/output/ \
  --file_type moldev \
  --test_image_count 2 \
  --slurm_queue <your_partition> \
  --max_cpus 32 \
  --max_memory 128.GB
```

Placeholders to substitute:

- `<your-scratch>` — your cluster's scratch path (see the note above).
- `<your_partition>` — your SLURM partition/queue name. **Omit `--slurm_queue` entirely** to use the cluster default partition.
- `--max_cpus` / `--max_memory` — set to the largest node you can request; the pipeline clamps per-process requests to these.

Prefer containers on HPC? Build them once (see [Option 3](#option-3-singularity--apptainer-build-your-own-containers)) and swap `conda` for `singularity`:

```bash
nextflow run main.nf \
  -profile singularity,slurm_generic \
  --singularity_path /path/to/your/containers \
  -work-dir <your-scratch>/nextflow-work/lizard-wizard \
  --input_dir /path/to/images/ \
  --output_dir /path/to/output/ \
  --slurm_queue <your_partition> --max_cpus 32 --max_memory 128.GB
```

### AWS Batch

Run on [AWS Batch](https://www.nextflow.io/docs/latest/aws.html) with the `awsbatch` profile. This requires AWS infrastructure you set up in advance:

- An **S3 bucket** for the Nextflow work directory.
- An **AWS Batch compute environment** and a **job queue**.
- **IAM** permissions for Batch, EC2, ECR/Docker, and S3 (see the [nf-core AWS Batch guide](https://nf-co.re/docs/usage/getting_started/aws-batch) for a battle-tested setup).
- A **container image** for each process (Docker), since Batch jobs run in containers.

Provide your AWS settings via params or environment variables (all placeholders — `# replace with your own`):

```bash
nextflow run main.nf \
  -profile awsbatch \
  --aws_region us-east-1 \
  --aws_queue my-batch-job-queue \
  --aws_workdir s3://my-bucket/lizard-wizard-work \
  --input_dir s3://my-bucket/images/ \
  --output_dir s3://my-bucket/lizard-wizard-out/ \
  --file_type moldev \
  --test_image_count 2
```

The matching environment-variable form (handy for CI):

```bash
export AWS_REGION=us-east-1
export LZW_AWS_QUEUE=my-batch-job-queue
export LZW_AWS_WORKDIR=s3://my-bucket/lizard-wizard-work
# Path to the AWS CLI *inside* your Batch image (nf-core default shown):
export LZW_AWS_CLI_PATH=/home/ec2-user/miniconda/bin/aws
```

> **Container images required.** Batch jobs run inside containers, and Lizard Wizard does not publish images. Build and push an image per environment (see [Docker](#option-2-docker)) to a registry AWS can pull from (e.g. Amazon ECR), then combine your image-mapping profile with `awsbatch`, e.g. `-profile docker_custom,awsbatch`.
>
> The `awsbatch` profile ([`config/profiles.config`](./config/profiles.config)) sets `process.executor = 'awsbatch'`, `process.queue`, `aws.region`, and `aws.batch.cliPath`. The defaults are deliberate `CHANGE-ME` placeholders so a misconfigured run fails fast rather than writing to the wrong account. For deeper tuning (compute environments, spot instances, retries) see the Nextflow AWS docs linked above.

### GCP Batch

Run on [Google Cloud Batch](https://www.nextflow.io/docs/latest/google.html) with the `gcp` profile. This requires:

- A **GCP project** with the Batch and Compute APIs enabled.
- A **GCS bucket** for the Nextflow work directory.
- Authentication (`gcloud auth application-default login`, or a service-account key).
- A **container image** per process.

The profile defaults to Arc's project/region/bucket so internal runs keep working. **External users must override all three:**

```bash
nextflow run main.nf \
  -profile gcp \
  --gcp_project my-gcp-project \
  --gcp_region us-central1 \
  --gcp_workdir gs://my-bucket/lizard-wizard-work \
  --input_dir gs://my-bucket/images/ \
  --output_dir gs://my-bucket/lizard-wizard-out/ \
  --file_type moldev \
  --test_image_count 2
```

Equivalent environment variables:

```bash
export GCP_PROJECT=my-gcp-project
export GCP_REGION=us-central1
export GCP_WORKDIR=gs://my-bucket/lizard-wizard-work
```

> **Container images required.** Google Batch runs jobs in containers, and Lizard Wizard does not publish images. Build and push an image per environment (see [Docker](#option-2-docker)) to a registry GCP can pull from (e.g. Artifact Registry / GCR), then combine your image-mapping profile with `gcp`, e.g. `-profile docker_custom,gcp`.
>
> If you do not override the project/region/bucket, the run will target Arc's `arc-genomics` project / `gs://arc-genomics-nextflow` bucket and fail with a permissions error — that is expected. Always set `--gcp_project`, `--gcp_region`, and `--gcp_workdir`.

### Running on Arc's Chimera cluster (internal)

> **[Arc internal]** This section is for Arc Institute users on the Chimera HPC. Everyone else can skip it — the profiles below depend on Arc-only paths (`/scratch/<group>/<user>/...`, `/large_storage/...`) and a Chimera-specific SLURM queue.

The `chimera` and `chimera_singularity` profiles auto-resolve Arc paths:

- `chimera` → work dir `/scratch/<group>/<user>/nextflow-work/lizard-wizard`, conda cache `/home/<user>/nextflow/conda-cache/lizard-wizard`.
- The Chimera-tuned `slurm` profile uses queue `cpu_batch_high_mem` with `max_cpus = 80`, `max_memory = 900.GB`.
- Prebuilt containers live at `/large_storage/multiomics/public/singularity/lizard-wizard/`.

Conda on Chimera:

```bash
nextflow run main.nf \
  -profile conda,chimera,slurm \
  --input_dir /path/to/images/ \
  --output_dir /path/to/output/ \
  --test_image_count 2 \
  -N your.email@arcinstitute.org
```

Singularity on Chimera (uses the shared `.sif` directory):

```bash
nextflow run main.nf \
  -profile singularity,chimera_singularity,slurm \
  --singularity_path /large_storage/multiomics/public/singularity/lizard-wizard \
  --input_dir /path/to/images/ \
  --output_dir /path/to/output/ \
  --test_image_count 2
```

## Usage

### Recommended two-step run

We recommend a two-step approach regardless of environment. The examples use `-profile conda` locally; swap in your environment's profile (e.g. `conda,slurm_generic`, `awsbatch`, `gcp`) from [Running Lizard Wizard](#running-lizard-wizard).

1. **Spot check**: run on a few images first to verify parameters. This runs Lizard Wizard with preset parameters; we recommend reading the [Tutorial](docs/lizardwizard_tutorial.md) for how to adjust parameters for your dataset.

   ```bash
   nextflow run main.nf \
     -profile conda \
     --input_dir /path/to/image/files/ \
     --output_dir /path/to/output/location/ \
     --file_type moldev \
     --test_image_count 3
   ```

2. **Full run**: process the entire dataset, reusing completed work with `-resume`:

   ```bash
   nextflow run main.nf \
     -profile conda \
     --input_dir /path/to/image/files/ \
     --output_dir /path/to/output/location/ \
     --file_type moldev \
     -resume
   ```

> Add `-N you@example.com` to receive email notifications. This requires a reachable SMTP relay; configure yours with `LZW_MAIL_FROM` / `LZW_SMTP_HOST` / `LZW_SMTP_PORT` (see [`config/utils.config`](./config/utils.config)). If you skip `-N`, the pipeline runs normally.
>
> Add `-profile ...,report,trace` to write an HTML run report to `${output_dir}/nf-report/` and a per-task trace to `${output_dir}/nf-trace/`.

### Parameters

The pipeline has many configurable parameters that can be set via command line or config files. See [`nextflow.config`](./nextflow.config) or the [Tutorial](docs/lizardwizard_tutorial.md) for detailed information about setting these parameters for your specific data type.

Key parameters include:

- `--input_dir`: Path to input images
- `--output_dir`: Where to save results
- `--file_type`: Set to `moldev` or `zeiss` depending on your microscope
- `--use_2d`: Set to `true` for 2D images instead of 3D (default: `false`)
- `--test_image_count`: Number of random images to process for testing
- `--test_image_names`: Specify particular images to process (comma-separated)
- `--max_cpus` / `--max_memory` / `--max_time`: Per-process resource caps (lower these on small machines)

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
- Use a `-work-dir` on fast storage; add `-resume` for iterative runs.
- Record the exact command and Nextflow version used for each production run.

## Advanced Usage

- Batch processing: submit multiple Nextflow runs by condition, pointing to the same `-work-dir` and distinct `--output_dir` per condition.
- Custom parameters: use a Nextflow `-params-file params.json` to store a reusable configuration.
- Custom profiles: create site- or lab-specific profiles in [`config/profiles.config`](./config/profiles.config) for CPUs, memory, queue names, and container paths. Container images are mapped to the process labels `caiman_env`, `cellpose_env`, `summary_env`, and `wizards_staff_env` — point these at your own registry images if you publish them.

## Secrets (optional OpenAI integration)

**[Optional]** The pipeline can use `gpt-4o(-mini)` to write a short natural-language summary of the run's log files. This is a convenience feature only.

To enable it, set an `OPENAI_API_KEY` as a Nextflow secret (assuming `OPENAI_API_KEY` is set in your environment):

```bash
nextflow secrets set OPENAI_API_KEY $OPENAI_API_KEY
```

**You can safely skip this.** If you do not set `OPENAI_API_KEY`, the pipeline runs exactly the same and produces all the same scientific outputs — only the optional AI-written log *summary* will be blank. No core functionality, metrics, plots, or data files are affected.

## Quick Troubleshooting

- Nextflow not found: ensure you activated the env (`conda activate nextflow_env`).
- Pipeline stalls/fails: check `.nextflow.log` and `logs/` under `--output_dir`, then re-run with `-resume`.
- No neurons detected: lower `--min_corr`/`--min_pnr`, verify `--gSig` and masking outputs.
- Out of memory on a small machine: lower `--max_cpus`/`--max_memory` and `--test_image_count`.
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
- [Arc Institute](https://www.arcinstitute.org/) where Lizard Wizard was developed
