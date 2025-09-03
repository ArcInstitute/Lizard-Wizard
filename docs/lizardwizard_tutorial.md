
# Lizard Wizard Parameter Tutorial

This tutorial explains how to configure Lizard Wizard for optimal calcium signal detection and analysis. It includes a pre-run checklist, data preparation, a parameter selection decision flowchart, recommended starting values by data type, step-by-step workflows, timing guidance, and QC/validation tips.

## Table of Contents

- [Lizard Wizard Parameter Tutorial](#lizard-wizard-parameter-tutorial)
  - [Table of Contents](#table-of-contents)
  - [Parameters Overview](#parameters-overview)
  - [Before You Begin](#before-you-begin)
  - [Data Preparation Guidelines](#data-preparation-guidelines)
  - [Parameter Selection Flowchart](#parameter-selection-flowchart)
  - [Parameter Categories](#parameter-categories)
  - [Key Parameters Overview](#key-parameters-overview)
  - [Workflow Parameters](#workflow-parameters)
  - [Calcium Detection Parameters](#calcium-detection-parameters)
  - [Delta F/F Calculation Parameters](#delta-ff-calculation-parameters)
  - [Clustering Parameters](#clustering-parameters)
  - [Experimental Parameters](#experimental-parameters)
  - [Parameter Examples by Data Type NOTE THIS IS JUST PLACEHOLDER NUMBERS WE NEED TO UPDATE](#parameter-examples-by-data-type-note-this-is-just-placeholder-numbers-we-need-to-update)
    - [3D Organoid/Spheroid Imaging (Molecular Devices)](#3d-organoidspheroid-imaging-molecular-devices)
    - [2D Neuronal Culture (Molecular Devices)](#2d-neuronal-culture-molecular-devices)
    - [High-Magnification Zeiss Data](#high-magnification-zeiss-data)
  - [Step-by-Step Walkthrough](#step-by-step-walkthrough)
  - [Common Workflows](#common-workflows)
    - [2D culture analysis](#2d-culture-analysis)
    - [3D organoid analysis](#3d-organoid-analysis)
    - [Time-series analysis](#time-series-analysis)
    - [Multi-condition comparisons](#multi-condition-comparisons)
  - [Expected Processing Times](#expected-processing-times)
  - [Validation and Quality Control](#validation-and-quality-control)
  - [Simulation Data Parameters](#simulation-data-parameters)
  - [Troubleshooting Parameter Settings](#troubleshooting-parameter-settings)
    - [No Cells Detected](#no-cells-detected)
    - [Too Many False Positives](#too-many-false-positives)
    - [Missing Calcium Events](#missing-calcium-events)
    - [Component Merging Issues](#component-merging-issues)
    - [Slow Processing](#slow-processing)

## Parameters Overview

Lizard Wizard is designed to flexibly handle various types of calcium imaging data, from 2D time-lapse recordings to 3D organoid/spheroid imaging. The parameters described in this tutorial allow you to customize the pipeline for your specific experimental setup.

Before running the full pipeline, we recommend spot-checking a few images to verify parameter settings. Once optimized, you can confidently process your entire dataset.

Each parameter influences how calcium imaging data is processed and analyzed, enabling fine-tuning for your dataset. The Lizard-Wizard pipeline can be executed via the command line using [Nextflow](https://www.nextflow.io/). Below is an example of how to run the pipeline:

```bash
nextflow run main.nf \
  -profile conda,slurm \
  -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
  --input_dir /path/to/image/files/ \
  --output_dir /path/to/output/location/ \
  --test_image_count 3 \
  --OTHER_PARAMETERS 
  -N YOUR_EMAIL_HERE@arcinstitute.org
```

## Before You Begin

- Verify Nextflow and Java:
  - `nextflow -version` 
- Activate the environment: `conda activate nextflow_env`
- Ensure input images are accessible on the compute system (e.g., copied to `/scratch`/cluster storage).
- Confirm write access to `--output_dir` and enough space for intermediate files.

## Data Preparation Guidelines

- Set `--file_type` to match your imaging system: `moldev` or `zeiss`.
- Organize inputs so each acquisition or condition is in a clear directory.
- Avoid extremely long file names and special characters.
- For 3D organoids, keep voxel size metadata consistent across files.
- If motion is severe, consider preprocessing or higher frame rates.

## Parameter Selection Flowchart

```mermaid
flowchart TD
  A[Start: Know imaging modality?] -->|2D| B[Set --use_2d true]
  A -->|3D| C[Set --use_2d false]
  B --> D{Neuron size in pixels?}
  C --> D
  D -->|Small (3-5)| E[gSig 4-5]
  D -->|Medium (5-7)| F[gSig 5-7]
  D -->|Large (7-9)| G[gSig 7-8]
  E --> H[min_corr 0.75-0.85]
  F --> H
  G --> H
  H --> I[min_pnr 4-6; min_SNR 2.5-3.5]
  I --> J{Spot check 2-3 images}
  J -->|Too many FPs| K[increase min_corr/min_pnr/min_SNR]
  J -->|Missed events| L[decrease thresholds or zscore_threshold]
  K --> M[Re-run spot check]
  L --> M
  M --> N[Proceed to full run]
```

## Parameter Categories

Lizard Wizard parameters fall into several categories:

1. **Workflow Parameters**: Control the overall execution of the pipeline
2. **Calcium Detection Parameters**: Determine how calcium events are identified and analyzed
3. **Delta F/F Calculation Parameters**: Configure how fluorescence changes are calculated and normalized
4. **Clustering Parameters**: Adjust how neurons are grouped based on activity patterns
5. **Experimental Parameters**: Specific to simulations and test runs

## Key Parameters Overview

Here's a quick reference of the most commonly adjusted parameters by data type:

| Parameter | 2D Recordings | 3D Organoids | Large Field of View | Small Field of View |
|-----------|---------------|--------------|---------------------|---------------------|
| `--use_2d` | `true` | `false` | Any | Any |
| `gSig` | 4–6 | 6–8 | 6–9 | 4–6 |
| `decay_time` (s) | 0.35–0.5 | 0.5–0.7 | Any | Any |
| `min_SNR` | 2.5–3.5 | 3–4 | 2.5–3.5 | 3–4 |
| `min_corr` | 0.75–0.85 | 0.82–0.9 | 0.75–0.85 | 0.82–0.9 |
| `min_pnr` | 4–6 | 5–7 | 4–6 | 6–8 |
| `size_threshold` | 10000–15000 | 20000–30000 | 20000–30000 | 10000–15000 |

## Workflow Parameters

- **`-profile [profiles]`**:  
    Specifies the use of conda environments and SLURM as the job scheduler. Modify this depending on your local execution environment.
  - Example: `-profile conda,slurm,chimera`
  - Common options:
    - `conda`: Use conda environments
    - `slurm`: Use SLURM scheduler
    - `vm`: Local execution
    - `chimera`: Parameters for the Chimera cluster

- **`-work-dir`**:  
  Defines the working directory where intermediate files will be stored. Adjust this path as needed for your system. The example above places the files in the user's scratch directory.

- **`input_dir`** (string):  
  Path to the directory on Chimera containing your input images. This is where the raw calcium imaging data files are located on Chimera. **Note: your images must be transferred from the NAS/local storage to Chimera for Lizard-Wizard to function correctly.**
  - Example: `"/path/to/input/images/"`

- **`output_dir`** (string):  
  Path to the directory where the output files will be saved on chimera. This includes .npy files of processed calcium traces, and images. This will be the path specified for analysis by the related Calcium Imaging analysis package Wizards-Staff.  
  - Example: `"/path/to/output/results/"`

- **`test_image_count`** (integer):  
  Number of random images used for a spot check. If set to `0`, spot check phase is skipped and all images in the directory are processed. Note it is recommended to spot check at a few images to ensure that parameter settings are finished before proceeding with the entire image set.
  - Example: `10` to test 10 random images, `0` to use all available images.
  - Default: `0`

- **`--test_image_names`** (list, comma-separated):  
  Alternatively, you can specify particular images to process by providing their base file names in a comma-separated list. If left as `null`, no specific images are pre-selected. For example:
  
  \`\`\`bash
  --test_image_names 10xGCaMP-6wk-F08_s1_FITC,10xGCaMP-6wk-D10_s1_FITC
  \`\`\`

- **`-N YOUR_EMAIL_HERE@arcinstitute.org`**:  
  Provides an email address to receive pipeline status updates (e.g., error notifications and completion messages). While optional, it's highly recommended for monitoring long-running jobs. Be sure to replace `YOUR_EMAIL_HERE@arcinstitute.org` with your actual email address.

## Calcium Detection Parameters

The user is responsible for specifying several key parameters for the identification and filtering of calcium events within their images. While some of these parameters are driven by biological factors (e.g., decay_time, gSig) and imaging setup (e.g., tsub, ssub), tuning them is left to the researcher's discretion during the spot check phase of the pipeline. Below is a list of calcium event detection-specific parameters that can be set:

- **`--decay_time [float]`**:  
  Average decay time (in seconds) of calcium transients.
  - This affects the deconvolution model and should match your calcium reporter's dynamics
  - Lower values (0.3-0.5s) work well for faster GCaMP variants
  - Higher values (0.5-0.7s) for slower indicators or 3D recordings
  - Default: `0.5`

- **`--gSig [integer]`**:  
  Half-size (radius) of neurons in pixels.
  - This should correspond to the expected width/height of neurons in your images
  - For 40x objectives: typically 4-7 pixels
  - For 20x objectives: typically 3-5 pixels
  - For 10x objectives with organoids: typically 6-8 pixels
  - Default: `6`

- **`--rf [integer]`**:  
  Patch size for dividing the field of view.
  - Larger patches capture more context but increase computation time
  - Small FOV or high magnification: 30-40
  - Large FOV or low magnification: 40-60
  - Default: `40`

- **`--min_SNR [float]`**:  
  Minimum signal-to-noise ratio for transient detection.
  - Higher values (4-5) are more conservative, detecting only clear signals
  - Lower values (2-3) detect more events but may include false positives
  - Default: `3`

- **`--r_values_min [float]`**:  
  Minimum threshold for spatial consistency.
  - Measures how well detected components match the raw data
  - Higher values (0.85-0.95) enforce stricter consistency
  - Default: `0.85`

- **`--tsub [integer]`**:  
  Temporal downsampling factor.
  - Reduces temporal resolution to speed up processing
  - High frame rate data (>20 fps) often benefits from tsub=2
  - Default: `2`

- **`--ssub [integer]`**:  
  Spatial downsampling factor.
  - Reduces spatial resolution to speed up processing
  - High resolution data often benefits from ssub=2
  - Default: `2`

- **`--p_th [float]`**:  
  Percentile threshold for background noise reduction.
  - Higher values (80-90) are more aggressive at removing background
  - Lower values (50-70) retain more signal but may include noise
  - Default: `0.75` (75%)

- **`--min_corr [float]`**:  
  Minimum peak correlation value to retain components.
  - Higher values (0.85-0.95) are more selective
  - Lower values (0.7-0.8) detect more components but may include artifacts
  - Default: `0.8`

- **`--min_pnr [float]`**:  
  Minimum peak-to-noise ratio to identify significant components.
  - Higher values (6-8) detect only very clear signals
  - Lower values (3-5) include more subtle signals
  - Default: `5`

- **`--ring_size_factor [float]`**:  
  Scales the exclusion ring size during ROI detection.
  - Calculated as `gSig * ring_size_factor`
  - Larger values help separate nearby neurons
  - Default: `1.4`

## Delta F/F Calculation Parameters

These parameters control how baseline fluorescence is determined and normalized:

- **`--f_baseline_perc [integer]`**:  
  Percentile value used for filtering when calculating delta F/F.
  - Lower values (5-10) are more sensitive to fast changes
  - Higher values (15-30) produce more stable baselines but may miss small events
  - Default: `8` (8th percentile)

- **`--win_sz [integer]`**:  
  Window size for the percentile filter.
  - Larger windows provide more stable baselines but may miss slow trends
  - Smaller windows track baseline more closely but can be affected by noise
  - Default: `500` frames

## Clustering Parameters

These parameters control how neurons are grouped based on activity patterns:

- **`--min_clusters [integer]`**:  
  Minimum number of clusters to try.
  - Default: `2`

- **`--max_clusters [integer]`**:  
  Maximum number of clusters to try.
  - Default: `10`

- **`--size_threshold [integer]`**:  
  Size threshold for filtering out noise events.
  - Higher values (>20000) filter more aggressively
  - 3D organoids typically need 20000-30000
  - 2D cultures typically need 10000-20000
  - Default: `20000`

- **`--percentage_threshold [float]`**:  
  Percentage threshold for FWHM calculation.
  - Default: `0.2`

- **`--zscore_threshold [integer]`**:  
  Z-score threshold for detecting significant events.
  - Higher values (4-5) detect only very clear events
  - Lower values (2-3) detect more subtle events
  - Default: `3`

## Experimental Parameters

These parameters relate to cell segmentation and image masking:

- **`--min_object_size [integer]`**:  
  Minimum size (in pixels) for successful segmentation.
  - Default: `500`

- **`--max_segment_retries [integer]`**:  
  Maximum retries for segmentation.
  - Default: `3`

- **`--start_diameter [integer]`**:  
  Starting diameter for mask segmentation.
  - Default: `300`

- **`--diameter_step [integer]`**:  
  Step size to increase diameter after failed segmentation.
  - Default: `200`

## Parameter Examples by Data Type NOTE THIS IS JUST PLACEHOLDER NUMBERS WE NEED TO UPDATE

These are recommended starting points that have worked well on representative datasets. Always spot check and fine-tune for your imaging conditions.

### 3D Organoid/Spheroid Imaging (Molecular Devices)

```bash
nextflow run main.nf \
  -profile conda,slurm \
  --input_dir /path/to/organoid/images/ \
  --output_dir /path/to/output/location/ \
  --file_type moldev \
  --use_2d false \
  --gSig 7 \
  --decay_time 0.6 \
  --min_SNR 3.5 \
  --min_corr 0.85 \
  --min_pnr 6 \
  --size_threshold 25000 \
  --test_image_count 2
```

### 2D Neuronal Culture (Molecular Devices)

```bash
nextflow run main.nf \
  -profile conda,slurm \
  --input_dir /path/to/2D/cultures/ \
  --output_dir /path/to/output/location/ \
  --file_type moldev \
  --use_2d true \
  --gSig 5 \
  --decay_time 0.4 \
  --min_SNR 2.5 \
  --min_corr 0.75 \
  --min_pnr 4 \
  --size_threshold 12000 \
  --test_image_count 2
```

### High-Magnification Zeiss Data

```bash
nextflow run main.nf \
  -profile conda,slurm \
  --input_dir /path/to/zeiss/images/ \
  --output_dir /path/to/output/location/ \
  --file_type zeiss \
  --gSig 4 \
  --decay_time 0.5 \
  --min_SNR 3 \
  --min_corr 0.8 \
  --min_pnr 5 \
  --size_threshold 15000 \
  --test_image_count 2
```

## Step-by-Step Walkthrough

1. Spot check 2–3 images with conservative thresholds:

   ```bash
   nextflow run main.nf \
     -profile conda,slurm \
     -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
     --input_dir /data/exp1/cultures/ \
     --output_dir /data/exp1/outputs/run1/ \
     --file_type moldev \
     --test_image_count 3 \
     --gSig 5 --min_corr 0.8 --min_pnr 5 --min_SNR 3 \
     -N your.email@example.com
   ```

2. Inspect QC images and traces in `caiman/`, `caiman_calc-dff-f0/`, and `wizards-staff/` under the output directory.

3. Adjust parameters using the [flowchart](#parameter-selection-flowchart) guidance.

4. Run the full dataset with `-resume`:

   ```bash
   nextflow run main.nf \
     -profile conda,slurm \
     -work-dir /scratch/$(id -gn)/$(whoami)/nextflow-work/lizard-wizard \
     --input_dir /data/exp1/cultures/ \
     --output_dir /data/exp1/outputs/run1/ \
     -resume
   ```

## Common Workflows

### 2D culture analysis

- Use `--use_2d true`, `gSig 4–6`, `decay_time 0.35–0.5`.
- Optimize `min_corr` and `min_pnr` to balance sensitivity vs specificity.
- Downsample (`tsub=2`, `ssub=2`) if processing time is high.

### 3D organoid analysis

- Use `--use_2d false`, `gSig 6–8`, `decay_time 0.5–0.7`.
- Increase `size_threshold` to remove small artifacts.
- Expect longer processing and higher memory use.

### Time-series analysis

- For long movies, increase `win_sz` for stable ΔF/F₀ baselines.
- Verify stability in `*_df-f0-graph.png` and denoised traces.

### Multi-condition comparisons

- Keep parameters identical across conditions.
- Export Wizards Staff CSVs (`frpm-data.csv`, `fwhm-data.csv`, `rise-time-data.csv`, correlations) for statistical analysis.

## Expected Processing Times

- Small 2D (100–200 frames, 512×512): 5–15 minutes per sample
- Large 2D (500–1000 frames, 1024×1024): 15–45 minutes per sample
- 3D organoids (500–1000 frames, large FOV): 30–90+ minutes per sample

Actual times depend on hardware, `-cpus`, and storage performance.

## Validation and Quality Control

- Review `*_cnm-A.npy` footprints with montages for anatomical plausibility.
- Confirm clear calcium transients in `*_cnm-traces.png` and `*_cnm-denoised-traces.png`.
- Check ΔF/F₀ traces in `*_df-f0-graph.png` for baseline stability.
- Use Wizards Staff plots to verify clustering structure and spatial activity overlays.
- If QC fails, revisit `gSig`, `min_corr`, `min_pnr`, and downsampling.

## Simulation Data Parameters

For users getting started with Lizard Wizard, we provide tools to generate simulated calcium imaging data. This helps understand parameter settings before applying them to real data:

```bash
nextflow run main.nf \
  -profile dev_moldev_2d_sim,vm,conda \
  --num_simulations 3 \
  --num_frames 500 \
  --puff_intensity 7 \
  --num_puffs 20 \
  --img_width 256 \
  --img_ht 256 \
  --noise_free \
  --output_dir ./simulations/ \
  --base_fname synthetic_movie \
  --retries 3 \
  --delay 2 \
  --exposure_time 10
  --decay_time 0.5 \
  --gSig 6
```

Simulation-specific parameters:

- **`--num_simulations [integer]`**: Number of synthetic movies to generate
  - Default: `1`

- **`--num_frames [integer]`**: Total frames in each simulated movie
  - Default: `1000`

- **`--puff_intensity [integer]`**: Amplitude of simulated calcium "puffs"
  - Default: `5`

- **`--num_puffs [integer]`**: Number of calcium events to simulate
  - Default: `10`

- **`--img_width [integer]`**: Width in pixels of simulated frames
  - Default: `128`

- **`--img_ht [integer]`**: Height in pixels of simulated frames
  - Default: `128`

- **`--noise_free`**: Generate noise-free movies (omit for realistic noise)

- **`--exposure_time [integer]`**: Simulated exposure time in seconds
  - Default: `8`

## Troubleshooting Parameter Settings

If you encounter issues with your parameter settings, here are some common adjustments:

### No Cells Detected

- Increase `--start_diameter` and `--min_object_size`
- Decrease `--min_corr` and `--min_pnr`
- Check that `--gSig` matches the approximate neuron radius in your images

### Too Many False Positives

- Increase `--min_SNR` and `--min_pnr`
- Increase `--size_threshold` to filter out small noise events
- Increase `--min_corr` for stricter component selection

### Missing Calcium Events

- Decrease `--min_SNR`
- Decrease `--zscore_threshold`
- Adjust `--f_baseline_perc` to a lower value (5-10)

### Component Merging Issues

- Increase `--ring_size_factor` to better separate nearby neurons
- Increase `--min_corr` to enforce spatial consistency

### Slow Processing

- Increase `--tsub` and `--ssub` for faster processing (at cost of resolution)
- Decrease `--gSig` if your neurons are smaller than the default

For additional help, examine the log files and visualizations in the output directory to identify where the pipeline may be performing suboptimally.
