#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import logging
import argparse
import xml.etree.ElementTree as ET
## 3rd party
import numpy as np
import matplotlib.pyplot as plt
import tifffile
import caiman as cm
from caiman.source_extraction import cnmf
from caiman.utils.visualization import inspect_correlation_pnr, nb_inspect_correlation_pnr
from caiman.utils.visualization import plot_contours, nb_view_patches, nb_plot_contour
# source 
from load_tiff import load_tiff_metadata, get_metadata_value, extract_exposure
from caiman_plot_traces import plot_original_traces, plot_denoised_traces


# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Run Caiman on image"
epi = """DESCRIPTION:
Run Caiman on a single image file. 
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('img_file', type=str,
                    help='Directory path containing the image files')
parser.add_argument('--output-dir', type=str, default="caiman_output",
                    help='Output directory')
parser.add_argument('-g', '--gSig', type=int, default=6,
                    help='Size of the Gaussian filter')
parser.add_argument('--rf', type=int, default=40,
                    help='Size of patches for the correlation image')
parser.add_argument('--decay-time', type=float, default=0.5,
                    help='Average decay time of a transient')
parser.add_argument('--tsub', type=int, default=2,
                    help='Temporal subsampling factor')
parser.add_argument('--ssub', type=int, default=2,
                    help='Spatial subsampling factor')
parser.add_argument('-p', '--processes', type=int, default=1,
                    help='Number of processes to use')
parser.add_argument('--motion-correct', action='store_true', default=False,
                    help = 'Perform motion correction')

# functions
def setup_cluster(processes: int=1) -> int:
    """
    Sets up a new cluster for parallel processing using the CaImAn library.

    This function first checks if there is an existing cluster and attempts to close it if found.
    It then sets up a new cluster using all but one of the available CPU cores.

    Args:
        processes: The number of processes to use in the new cluster. If not specified, the function will use all but one of the available CPU cores.
    Returns:
        n_processes: The number of processes successfully initialized in the new cluster.
    """
    # Initialize the global cluster variable
    global cluster
    cluster = None

    # Stop the existing cluster if it exists
    if cluster is not None:
        logging.info("Attempting to close the existing cluster...")
        try:
            # Stop the existing cluster
            cm.stop_server(dview=cluster)
            logging.info("  Previous cluster closed successfully.")
        except Exception as e:
            logging.warning(f"  Failed to close the previous cluster: {str(e)}")
        cluster = None
    
    # Set up a new cluster
    logging.info("Setting up a new cluster...")
    n_processes = 0  # Initialize n_processes
    try:
        # Set up a new cluster with the specified number of processes
        _, cluster, n_processes = cm.cluster.setup_cluster(
            backend="multiprocessing", 
            n_processes=processes, 
            ignore_preexisting=True
        )
        logging.info(f"  Successfully set up a new cluster with {n_processes} processes")
    except Exception as e:
        logging.warning(f"  Error during cluster setup: {str(e)}")
    # Return the number of processes
    return n_processes

def close_cluster():
    """
    Closes the existing cluster if one is running.

    This function attempts to stop the existing cluster and catches any exceptions that might occur.
    If no cluster is found, it prints a message indicating that there is no cluster to close.
    """
    global cluster
    if cluster is not None:
        logging.info("Closing the cluster...")
        try:
            # Stop the existing cluster
            cm.stop_server(dview=cluster)
            logging.info("  Cluster closed successfully.")
        except Exception as e:
            logging.warning(f"  Failed to close the cluster: {str(e)}")
        finally:
            cluster = None
    else:
        logging.info("No cluster to close.")

def plot_correlations(cn_filter, pnr, output_dir: str) -> None:
    """
    Plots the correlation and peak-to-noise ratio images side by side.

    Args:
        cn_filter: The correlation image data
        pnr: The peak-to-noise ratio image data
        output_dir: The output directory to save the plots
    """
    logging.info("Plotting correlation and peak-to-noise ratio images...")
    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    # Create a plot of the correlation and peak-to-noise ratio images
    inspect_correlation_pnr(cn_filter, pnr)
    ## Save the plot
    outfile = os.path.join(output_dir, 'correlation_pnr.png')
    plt.savefig(outfile)
    plt.close()
    logging.info(f"Correlation and peak-to-noise ratio images saved to {outfile}")
            
    # Create two subplots side by side to show corr and pnr histograms
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
            
    # Histogram for cn_filter
    counts1, bins1, patches1 = axes[0].hist(
        np.concatenate(cn_filter), 
        bins=30, 
        orientation='horizontal', 
        color='blue', 
        edgecolor='black'
    )
    axes[0].invert_xaxis()
    axes[0].set_title('Histogram of CN Filter')
    axes[0].set_xlabel('Count')
    axes[0].set_ylabel('Correlation Value')
            
    # Histogram for pnr
    counts2, bins2, patches2 = axes[1].hist(
        np.concatenate(pnr), 
        bins=30, 
        orientation='horizontal', 
        color='green', 
        edgecolor='black'
    )
    axes[1].invert_xaxis()
    axes[1].set_title('Histogram of pnr')
    axes[1].set_xlabel('Count')
    axes[1].set_ylabel('pnr')
            
    # Save the plot of pnr and corr filter
    outfile = os.path.join(output_dir, 'histogram_pnr_cn_filter.png')
    plt.savefig(outfile, format='tiff')
    #plt.close() 
    logging.info(f"Histogram of correlation and peak-to-noise ratio images saved to {outfile}")
    logging.getLogger('matplotlib').setLevel(logging.INFO)

def run_caiman(im, frate: float, decay_time: float, gSig: int, rf: int, 
               tsub: int, ssub: int, n_processes: int,  motion_correct=False):
    """
    Run the CaImAn CNMF algorithm on the given image data.
    Args:
        im: numpy array of the image data
        frate: The imaging rate in frames per second
        decay_time: length of a typical transient in seconds
        gSig: gaussian width of a 2D gaussian kernel (~1/2 width neuron (pixels))
        rf: half-size of the patches in pixels. e.g., if rf=40, patches are 80x80
        tsub: temporal subsampling factor
        ssub: spatial subsampling factor
        n_processes: number of processes to use
        motion_correct: flag for performing motion correction 
    Returns:
        cnm: The CNMF object containing the results of the CNMF algorithm
    """
    logging.info("Running Caiman...")
    
    # Set logging level for CaImAn
    logging.getLogger("caiman").setLevel(logging.ERROR)

    # Set various parameters for the CaImAn execution             
    p = 1                        # order of the autoregressive system
    K = None                     # upper bound on number of components per patch, in general None
    Ain = None                   # possibility to seed with predetermined binary masks
    gSiz = 4 * gSig + 1          # average diameter of a neuron, in general 4*gSig+1
    stride_cnmf = gSiz + 5       # overlap between patches (pixels) keep >gSiz
    merge_thresh = .7            # merging threshold, max correlation allowed
    low_rank_background = None   # None leaves background of each patch intact
    gnb = -1                     # number of background components (rank) if positive,
    nb_patch = 0                 # number of background components (rank) per patch if gnb>0,
    min_corr = .8                # min peak value from correlation image
    min_pnr = 5                  # min peak to noise ration from PNR image
    ssub_B = 1                   # additional downsampling factor in space for background
    ring_size_factor = 1.4       # radius of ring is gSiz*ring_size_factor
    min_SNR = 3           
    r_values_min = 0.85   
    epsilon = 1e-8               # small epsilon to avoid division by zero in PNR calculation

    # Initialize the CNMF model with the specified parameters
    cnm = cnmf.CNMF(
        n_processes=n_processes,
        method_init="corr_pnr",              # use this for 1 photon        
        k=K,
        gSig=(gSig, gSig),
        gSiz=(gSiz, gSiz),
        merge_thresh=merge_thresh,
        p = p,
        dview = cluster,
        tsub = tsub,
        ssub = ssub,
        Ain = Ain,
        rf = rf,
        stride = stride_cnmf,
        only_init_patch = True,                # set it to True to run CNMF-E         
        gnb = gnb,
        nb_patch = nb_patch,
        method_deconvolution = "oasis",        # could use 'cvxpy' alternatively
        low_rank_background = low_rank_background,
        update_background_components = True,   # sometimes setting to False improve the results
        min_corr = min_corr,
        min_pnr = min_pnr,
        normalize_init = False,                # just leave as is             
        center_psf = True,                     # leave as is for 1 photon                    
        ssub_B = ssub_B,
        ring_size_factor = ring_size_factor,
        del_duplicates = True,                 # whether to remove duplicates from initialization
        border_pix = 0                         # number of pixels to not consider in the borders
    ) 
    # Fit the model to the data
    cnm.fit(im)
    # set parameters for component evaluation
    cnm.params.set("quality", {"min_SNR": min_SNR, "rval_thr": r_values_min, "use_cnn": False})
    return cnm

def cnm_eval_estimates(cnm, Y, frate: float, base_fname: str, output_dir: str) -> None:
    """
    Evaluate the CNMF estimates and save the results to the specified output directory.
    Args:
        cnm: The CNMF object containing the results of the CNMF algorithm
        Y: The image data
        frate: The imaging rate in frames per second
        base_fname: The base filename of the input image
        output_dir: The output directory to save the CNMF output
    """
    logging.info("Evaluating CNMF estimates...")

    # Evaluate the components
    cnm.estimates.evaluate_components(Y, cnm.params)
    logging.info(f"Number of total components: {len(cnm.estimates.C)}")
    logging.info(f"Number of accepted components: {len(cnm.estimates.idx_components)}")

    # Get the index of accepted components
    idx = cnm.estimates.idx_components
            
    # Save the indices of accepted components
    np.save(os.path.join(output_dir, f"{base_fname}_cnm_idx.npy"), idx)

    # Plot original traces stacked on top of each other and the denoised traces
    if len(cnm.estimates.C) > 0:
        plot_original_traces(cnm.estimates, idx, cnm.estimates.YrA, frate)
        plot_denoised_traces(cnm.estimates, idx, frate)
    else:
        logging.warning("No components found to plot traces")

def save_caiman_output(cnm, cn_filter, pnr, base_fname: str, output_dir: str) -> None:
    """
    Save the output of the CNMF algorithm to the specified output directory.
    Args:
        cnm: The CNMF object containing the results of the CNMF algorithm
        cn_filter: The correlation image data
        pnr: The peak-to-noise ratio image data
        base_fname: The base filename of the input image
        output_dir: The output directory to save the CNMF output
    """
    logging.info("Saving CNMF output...")

    # Save the spatial footprint of the neurons detected by CNMF
    np.save(os.path.join(output_dir, f"{base_fname})_cnm_A.npy"), cnm.estimates.A.todense())
            
    # Save the temporal components (i.e., the calcium activity over time) of neurons detected by CNMF
    np.save(os.path.join(output_dir, f"{base_fname}_cnm_C.npy"), cnm.estimates.C)
            
    # Deconvolved neural activity or spike estimates
    # is array, each row=neuron and each column=time point.
    np.save(os.path.join(output_dir, f"{base_fname}_cnm_S.npy"), cnm.estimates.S)
            
    # Save correlation and PNR images
    np.save(os.path.join(output_dir, f"{base_fname}_cn_filter.npy"), cn_filter)
    np.save(os.path.join(output_dir, f"{base_fname}_pnr_filter.npy"), pnr)
    tifffile.imwrite(os.path.join(output_dir, f"{base_fname}_cn_filter.tif"), cn_filter)
    tifffile.imwrite(os.path.join(output_dir, f"{base_fname}_pnr_filter.tif"), pnr)
            
def main(args):
    # get the frame rate
    frate = os.environ["FRATE"]
    logging.info(f"Frame rate set to: {frate}")

    # Create a memory-mapped file using CaImAn from the temp file
    fname_new = cm.save_memmap([args.img_file], base_name="memmap_", order="C")
  
    # Load the memory-mapped file
    Yr, dims, T = cm.load_memmap(fname_new)
    Y = Yr.T.reshape((T,) + dims, order="F")

    # Set up the cluster
    n_processes = setup_cluster(args.processes)

    # Set output
    os.makedirs(args.output_dir, exist_ok=True)
    base_fname = os.path.basename(os.path.splitext(args.img_file)[0])

    # Compute correlation and peak-to-noise ratio images
    logging.info("Computing correlation and peak-to-noise ratio images...")
    cn_filter, pnr = cm.summary_images.correlation_pnr(Y, gSig=args.gSig, swap_dim=False)

    # Plot the correlation and peak-to-noise ratio images
    plot_correlations(cn_filter, pnr, args.output_dir)

    # Run Caiman
    try:
        cnm = run_caiman(
            Y, 
            frate=frate, 
            decay_time=args.decay_time,
            gSig=args.gSig,
            rf=args.rf,
            tsub=args.tsub,
            ssub=args.ssub,
            n_processes=n_processes,
            motion_correct=args.motion_correct
        )
    finally: 
        # Regardless of whether the CNMF algorithm runs successfully or not, close the cluster
        close_cluster()

    # Check if any components were found
    if cnm.estimates.C.shape[0] == 0:
        logging.error(f"No components found in file {base_fname}")

    # Save the output  
    save_caiman_output(cnm, cn_filter, pnr, base_fname, args.output_dir)

    # Set the estimates
    cnm_eval_estimates(cnm, Y, frate, base_fname, args.output_dir)
    
    # Visualize the patches
    if len(cnm.estimates.C) > 0:
        logging.info("Visualizing patches...")
        nb_view_patches(
            Yr, 
            cnm.estimates.A.tocsc(), 
            cnm.estimates.C, 
            cnm.estimates.b, 
            cnm.estimates.f,
            dims[0], 
            dims[1], 
            YrA=cnm.estimates.YrA, 
            image_neurons=cn_filter,
            denoised_color="red", 
            thr=0.8, 
            cmap="gray"
        )
    else:
        logging.warning("No components found to visualize patches")

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)