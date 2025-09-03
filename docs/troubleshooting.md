# Lizard Wizard Troubleshooting Guide

This guide addresses common issues you might encounter when running the Lizard Wizard pipeline and provides solutions to help get your analysis back on track.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Pipeline Execution Issues](#pipeline-execution-issues)
- [Masking Problems](#masking-problems)
- [Calcium Signal Detection Issues](#calcium-signal-detection-issues)
- [Processing Performance Issues](#processing-performance-issues)
- [Results Interpretation Issues](#results-interpretation-issues)
- [Common Error Messages](#common-error-messages)
- [Getting Help](#getting-help)
 - [Singularity-specific Issues](#singularity-specific-issues)

## Installation Issues

### Conda Environment Creation Failures

**Problem:** Errors when creating conda environments during first pipeline run.

**Solutions:**
- Ensure you're using mamba instead of conda (much faster and more reliable)
- Try updating conda: `conda update -n base conda`
- Clear the conda cache: `conda clean --all`
- Check for conflicting environments: `conda env list`

### Nextflow Installation Issues

**Problem:** Nextflow not found or not executable.

**Solutions:**
- Verify Nextflow is installed: `nextflow -version`
- Ensure Nextflow environment is activated: `mamba activate nextflow_env`
- Check for Java installation (required by Nextflow): `java -version`
- Re-install Nextflow: `mamba install -c bioconda nextflow`

### Repository Cloning Problems

**Problem:** Unable to clone the repository or access errors.

**Solutions:**
- Verify your SSH key is set up correctly with GitHub
- Try HTTPS instead: `git clone https://github.com/ArcInstitute/Lizard-Wizard.git`
- Check GitHub access: `ssh -T git@github.com`

## Pipeline Execution Issues

### Pipeline Won't Start

**Problem:** Pipeline doesn't start or errors immediately.

**Solutions:**
- Check that input paths exist and are accessible
- Verify output directory is writable
- Ensure correct syntax for parameters: `-profile` (not `--profile`)
- Make sure Nextflow environment is activated
- Run with verbose logging: `nextflow run main.nf -log execution.log [your params]`

### Pipeline Fails Midway

**Problem:** Pipeline starts but fails during execution.

**Solutions:**
- Check error messages in `.nextflow.log` and in terminal output
- Look at process-specific logs in the work directory
- Make sure you have sufficient disk space for temporary files
- Use the `-resume` flag to continue from the point of failure
- Increase resource allocations if processes are running out of memory

### Work Directory Issues

**Problem:** Errors related to work directory or permissions.

**Solutions:**
- Specify an explicit work directory: `-work-dir /path/to/work`
- Ensure the work directory has sufficient space (100GB+ recommended)
- Check permissions: `ls -la /path/to/work`
- Clear the work directory if it's corrupted: `rm -rf /path/to/work/*`

## Masking Problems

### No Masks Generated

**Problem:** The pipeline fails to generate masks or creates empty mask files.

**Solutions:**
- Adjust masking parameters:
  - Increase `--start_diameter` (try 400-600)
  - Reduce `--min_object_size` (try 300)
  - Increase `--max_segment_retries` (try 5)
- Check your images for contrast issues
- Try preprocessing your images to enhance contrast
- For 2D data, set `--use_2d true`

### Poor Quality Masks

**Problem:** Masks are generated but don't properly capture the cells/organoids.

**Solutions:**
- Adjust `--start_diameter` to match your typical sample size
- Try increasing `--diameter_step` for more thorough parameter exploration
- Examine `*_masked-plot.tif` to see what went wrong
- For complex samples, consider pre-segmenting your images with other tools

### Masks Include Background

**Problem:** Masks capture too much background or non-cellular regions.

**Solutions:**
- Increase `--min_object_size` to filter out small artifacts
- Check sample preparation and imaging settings
- Try manual preprocessing to enhance contrast before running the pipeline

## Calcium Signal Detection Issues

### No Neurons Detected

**Problem:** CaImAn doesn't identify any neurons or very few.

**Solutions:**
- Adjust neuron detection parameters:
  - Decrease `--min_corr` (try 0.6-0.7)
  - Decrease `--min_pnr` (try 3-4)
  - Ensure `--gSig` matches your neuron size
- Check the correlation and PNR images to see if signals are visible
- Verify that masking worked correctly
- Make sure calcium signals are present in your data

### Too Many False Positives

**Problem:** CaImAn identifies too many components that aren't real neurons.

**Solutions:**
- Make detection more stringent:
  - Increase `--min_corr` (try 0.85-0.95)
  - Increase `--min_pnr` (try 6-8)
  - Increase `--min_SNR` (try 4-5)
  - Increase `--r_values_min` (try 0.9-0.95)
- Examine the spatial components to identify patterns in false positives
- Check for motion artifacts or fluctuating background

### Merged Neurons

**Problem:** Multiple neurons are detected as single components.

**Solutions:**
- Adjust component separation:
  - Increase `--ring_size_factor` (try 1.6-2.0)
  - Decrease `--gSig` if neurons are smaller than expected
- Check imaging resolution (may need higher resolution)
- Consider reducing cell density in future experiments

### Missing Calcium Events

**Problem:** Known calcium events aren't detected in the output.

**Solutions:**
- Adjust event detection thresholds:
  - Decrease `--min_SNR` (try 2-2.5)
  - Adjust `--decay_time` to match your calcium indicator
  - Decrease `--zscore_threshold` (try 2)
- Check ΔF/F₀ calculation parameters:
  - Adjust `--f_baseline_perc` (try 5-15)
  - Increase `--win_sz` for smoother baselines
- Verify events are visible in raw data plots

## Processing Performance Issues

### Pipeline Runs Too Slowly

**Problem:** Analysis takes much longer than expected.

**Solutions:**
- Optimize processing parameters:
  - Increase `--tsub` and `--ssub` for faster downsampling (trade-off with resolution)
  - Reduce the FOV size if possible
  - Process fewer images at once
- Adjust resource allocation:
  - Increase `-cpus` parameter
  - Run on a more powerful compute node
- Check for disk I/O bottlenecks

### Memory Errors

**Problem:** Processes fail with out-of-memory errors.

**Solutions:**
- Process smaller batches of images
- Increase downsampling factors (`--tsub` and `--ssub`)
- For large datasets, try processing in chunks and merging results later

### Disk Space Issues

**Problem:** Pipeline fails due to insufficient disk space.

**Solutions:**
- Clear the work directory regularly
- Use `-profile` settings that clean up intermediate files
- Specify a work directory on a volume with more space
- Run with `-resume` to avoid recomputing completed steps

## Results Interpretation Issues

### Poor Quality Traces

**Problem:** Calcium traces show excessive noise or artifacts.

**Solutions:**
- Check raw data quality
- Adjust signal extraction parameters:
  - Increase `--min_SNR` and `--min_pnr`
  - Try different `--decay_time` values
- Look for mechanical or optical artifacts in original data
- Consider preprocessing for motion correction

### Clustering Issues

**Problem:** Clustering results don't show clear patterns or are inconsistent.

**Solutions:**
- Adjust clustering parameters:
  - Modify `--min_clusters` and `--max_clusters`
  - Try processing with different random seeds
- Filter data to include only high-quality signals
- Look for batch effects or artifacts affecting clustering
- Try alternative clustering methods on exported data

### Missing Metrics in Output

**Problem:** Expected metric files are missing or incomplete.

**Solutions:**
- Check logs for specific errors
- Verify that upstream processes completed successfully
- Make sure relevant parameters were set
- Run with debug flag to get more information: `--debug true`

## Common Error Messages

### "No matching files found in input directory"

**Solutions:**
- Verify the path to your input directory
- Check file extensions and format
- Make sure you have the correct `--file_type` set
- Look for permission issues on the input files

### "CaImAn failed with error code X"

**Solutions:**
- Check CaImAn logs for specific error messages
- Look for memory issues or parameter conflicts
- Verify that input data formats are as expected
- Try running with different CaImAn parameters

### "Mask segmentation failed after X retries"

**Solutions:**
- Adjust masking parameters as suggested in the [Masking Problems](#masking-problems) section
- Check your images for contrast and quality issues
- Verify that your cells/organoids are visible in the minimum projections
- Consider manual pre-segmentation for challenging samples

### "Work directory is locked by another Nextflow instance"

**Solutions:**
- Check for other running Nextflow processes: `ps aux | grep nextflow`
- Remove the lock file: `rm -f /path/to/work/.nextflow.pid`
- Specify a different work directory
- Wait for the other process to complete

## Singularity-specific Issues

### Container build fails for Wizards-Staff

**Problem:** `pip` git+ssh install fails during `singularity build`.

**Solutions:**
- Ensure network egress from build node; `git` and `openssh-client` are installed in the definition (`wizards_staff.def`).
- Prefer HTTPS with a read token: replace `git+ssh://git@github.com/...` with `git+https://<TOKEN>@github.com/...` in `envs/wizards_staff.yml`, or vendor a released tarball.

### Runtime cannot find mounted data paths

**Problem:** Processes cannot access `/large_storage` or `/scratch`.

**Solutions:**
- Use `-profile singularity,chimera` which sets `singularity.autoMounts = true`.
- If needed, add explicit binds: `singularity.runOptions = "-B /large_storage -B /scratch"` in a profile.

### GPU not detected inside container

**Problem:** CUDA/GPU libraries not visible.

**Solutions:**
- Run with `--nv`: set `process.containerOptions = '--nv'` for GPU-enabled processes or in a GPU profile.
- Ensure host nodes have compatible NVIDIA drivers and CUDA runtime.

### Conda solver failures during micromamba create

**Problem:** `micromamba create` fails with conflicts.

**Solutions:**
- Inspect `debug_*.json` artifacts generated by `./debug_dependencies.sh`.
- Align core pins (Python, numpy, scipy, tensorflow, opencv). For CaImAn, consider Python 3.10 and compatible numpy/scipy.
- Move `openai` to `pip` section in `envs/summary.yml` (conda often lacks this package/version).

## Getting Help

If you're still experiencing issues after trying the solutions in this guide:

1. **Check the logs**: Most problems can be diagnosed from the detailed logs in the output directory.

2. **Search GitHub Issues**: Check if someone has reported a similar problem: https://github.com/ArcInstitute/Lizard-Wizard/issues

3. **Create a new issue**: If your problem is not resolved, create a new issue with:
   - A clear description of the problem
   - The command you ran
   - Relevant error messages
   - Information about your computing environment
   - Any error messages included in the terminal output
   - A copy of the relevent log error files