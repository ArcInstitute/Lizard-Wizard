# How to detect Calcium signals using Lizard Wizard

This tutorial is relevant for researchers who record subcellular Ca2+ signals using fluorescent Ca2+ indicators. This algorithm automates the detection of these brief Ca2+ signals. Below, you'll find an explanation of each parameter and how to define them for your experiments.

## Parameters Overview

Each parameter controls different aspects of how calcium imaging data is processed and analyzed. Adjusting these parameters allows you to tailor the pipeline to your specific dataset. The `Lizard-Wizard` pipeline can be executed via the command line using [Nextflow](https://www.nextflow.io/). Below is an example of how to run the pipeline:

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

### (1) Key Flags

- **`-profile conda,slurm`**:  
  Specifies the use of conda environments and SLURM as the job scheduler. Modify this depending on your local execution environment.

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

### (2) Processing Options

- **`use_2d`** (boolean):  
  Set to `true` if you're processing 2D images or images where you are imaging samples which cover the entire field of view, or set `false` for organoid and spheroid 3d imaging set.
  - Default: `false`

- **`llm`** (string):  
  Specifies which language model to use for log summarization during the workflow.  
  - Options: `"gpt-4o-mini"` or `"gpt-4o"`  
  - Example: `"gpt-4o-mini"`

### (3) Calcium Detection Specific Parameters

The user is responsible for specifying several key parameters for the identification and filtering of calcium events within their images. While some of these parameters are driven by biological factors (e.g., `decay_time`, `gSig`) and imaging setup (e.g., `tsub`, `ssub`), tuning them is left to the researcher's discretion during the spot check phase of the pipeline. Below is a list of calcium event detection-specific parameters that can be set:

- **`decay_time`** (float):  
  The average decay time (in seconds) of a calcium transient. This parameter affects the deconvolution model and should be tuned based on the temporal dynamics of your calcium reporter.  
  - Default: `0.5` seconds.

- **`gSig`** (integer):  
  The half-size (radius) of neurons in the image. This should correspond to the expected height and width of the neurons in the field of view, in pixels.  
  - Default: `6`

- **Patch Size `rf`** (integer):  
  The size of each patch used to divide the FOV. This affects both the computation speed and the spatial resolution. Larger patches may capture more data but could take longer to process.
  - Default: `40`

- **`min_SNR`** (float):  
  Minimum signal-to-noise ratio (SNR) for transient detection. A higher SNR will detect more confident events but might miss smaller signals.  
  - Default: `3`

- **`r_values_min`** (float):  
  Minimum threshold for spatial consistency between the estimated components and the raw data.  
  - Default: `0.85`

- **`tsub`** (integer):  
  Temporal downsampling factor. Reduces the temporal resolution, which can speed up processing for large datasets.  
  - Default: `2`

- **`ssub`** (integer):  
  Spatial downsampling factor. Reduces the spatial resolution, which can speed up processing for large datasets.  
  - Default: `2`

- **`p_th`** (float):  
  Percentile threshold used during image processing. Controls the cutoff for background noise reduction.  
  - Default: `0.75`

- **`min_corr`** (float):  
  Minimum peak value from the correlation image to retain components.  
  - Default: `0.8`

- **`min_pnr`** (float):  
  Minimum peak-to-noise ratio from the PNR (Peak-to-Noise Ratio) image used to identify significant components.  
  - Default: `5`

- **`ring_size_factor`** (float):  
  This scales the size of the exclusion ring used during ROI detection. It is calculated as `gSig * ring_size_factor`.  
  - Default: `1.4`

### (4) Delta F/F Calculation Parameters

The calculation of delta F/F0 is essential for normalizing calcium fluorescence signals to detect relative changes in fluorescence, often reflecting neuronal activity. Two key parameters control the calculation process, helping define the baseline fluorescence (`F0`) and determine the window size for the filter applied to the signal:

- **`f_baseline_perc`** (integer):  
  The percentile value used for filtering when converting raw fluorescence data into delta F/F values.  
  - Default: `8` (for an 8th percentile filter).

- **`win_sz`** (integer):  
  The window size for the percentile filter used in the `calc_dff_f0` step.
  - Default: `500`

### (5) Simulation Data Parameters

For users getting started to work with Lizard-Wizard it is recommended to generate simulated calcium imaging data to help understand how to set parameters within your own images. These parameters allow you to define the characteristics of the simulated data, such as the number of frames, puff events, noise levels, and more. To generate simulation data, you can use a command like the following, in addition to calcium detection parameters set in previous section:

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
  --CALCIUM_DETECTION_PARAMETERS
```

- **`STK_file`** (string):  
  Path to the `.STK` file that contains the template data for simulation. This is the required input file, and the simulation will be based on its structure.  
  - Example: `"/path/to/STK/file.stk"`

- **`--num_simulations`** (integer):  
  The number of synthetic movies to simulate. This is useful for generating multiple datasets in one go.  
  - Default: `1`

- **`--num_frames`** (integer):  
  The total number of frames in each simulated movie. More frames will increase the duration of the movie but will require more computational resources.  
  - Default: `1000`

- **`--puff_intensity`** (integer):  
  The amplitude or intensity of the simulated calcium "puffs" in the data. Higher values will create larger, more noticeable puff events in the synthetic movie.  
  - Default: `5`

- **`--num_puffs`** (integer):  
  The number of calcium puff events to simulate within the movie.  
  - Default: `10`

- **`--img_width`** (integer):  
  The width (in pixels) of each frame in the simulated movie.  
  - Default: `128`

- **`--img_ht`** (integer):  
  The height (in pixels) of each frame in the simulated movie.  
  - Default: `128`

- **`--noise_free`** (flag):  
  If this flag is set (`True`), the simulation will generate a noise-free movie. By default, noise is included to simulate real-world conditions.  
  - Example: Use `--noise_free` to generate a noise-free movie.

- **`--output_dir`** (string):  
  Specifies the directory where the generated files will be saved. This must be a valid path on your system.  
  - Default: `'.'` (current directory)

- **`--base_fname`** (string):  
  The base file name to be used when saving the simulated movies. The file names will be suffixed with identifiers for each movie or trial.  
  - Default: `"synthetic_puffs"`

- **`--retries`** (integer):  
  The number of retry attempts for loading the `.STK` file. If the file fails to load due to a temporary issue, the system will attempt to load it again.  
  - Default: `5`

- **`--delay`** (integer):  
  The time (in seconds) to wait between retry attempts when loading the `.STK` file. This can be useful in case of network or file access delays.  
  - Default: `1`

- **`--exposure_time`** (integer):  
  The exposure time (in seconds) used in the simulation. This defines how long the "camera" is exposed for each frame, which can affect signal quality and intensity.  
  - Default: `8`