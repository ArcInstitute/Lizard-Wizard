#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import logging
import argparse
## 3rd party
import numpy as np
import matplotlib.pyplot as plt
import caiman as cm
from caiman.utils.visualization import inspect_correlation_pnr, nb_inspect_correlation_pnr
## source


#   decay_time         = 0.5      // the average decay time of a transient
#   gSig               = 6        // The expected half size of neurons (height, width)
#   rf                 = 40       // The size of patches for the correlation image
#   min_SNR            = 3        // Adaptive threshold for transient size
#   r_values_min       = 0.85     // Threshold for spatial consistency
#   use_2d             = false    // 2d image processing, instead of 3d

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Run Caiman on image"
epi = """DESCRIPTION:
   
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('img_file', type=str,
                    help='Directory path containing the image files')
parser.add_argument('--output-dir', type=str, default="caiman_output",
                    help='Output directory')
parser.add_argument('-g', '--gSig', type=int, default=6,
                    help='Size of the Gaussian filter')
parser.add_argument('-p', '--processes', type=int, default=1,
                    help='Number of processes to use')

# variables

# functions
def setup_cluster(processes: int=1):
    """
    Sets up a new cluster for parallel processing using the CaImAn library.

    This function first checks if there is an existing cluster and attempts to close it if found.
    It then sets up a new cluster using all but one of the available CPU cores.

    Returns:
    - processes: The number of processes successfully initialized in the new cluster.
    """
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
        logging.warning(f"Error during cluster setup: {str(e)}")
    # Return the cluster and the number of processes
    return n_processes

def plot_correlations(cn_filter, pnr, output_dir):
    """
    Plots the correlation and peak-to-noise ratio images side by side.
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
    #plt.show()
            
    # Create two subplots side by side to show corr and pnr histograms
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
            
    # Histogram for cn_filter
    counts1, bins1, patches1 = axes[0].hist(np.concatenate(cn_filter), bins=30, orientation='horizontal', color='blue', edgecolor='black')
    axes[0].invert_xaxis()
    axes[0].set_title('Histogram of CN Filter')
    axes[0].set_xlabel('Count')
    axes[0].set_ylabel('Correlation Value')
            
    # Histogram for pnr
    counts2, bins2, patches2 = axes[1].hist(np.concatenate(pnr), bins=30, orientation='horizontal', color='green', edgecolor='black')
    axes[1].invert_xaxis()
    axes[1].set_title('Histogram of pnr')
    axes[1].set_xlabel('Count')
    axes[1].set_ylabel('pnr')
            
    # Save the plot of pnr and corr filter
    outfile = os.path.join(output_dir, 'histogram_pnr_cn_filter.png')
    plt.savefig(outfile)
    plt.close() 
    logging.info(f"Histogram of correlation and peak-to-noise ratio images saved to {outfile}")
    logging.getLogger('matplotlib').setLevel(logging.INFO)

def main(args):
    # Create a memory-mapped file using CaImAn from the temp file
    fname_new = cm.save_memmap([args.img_file], base_name='memmap_', order='C')
  
    # Load the memory-mapped file
    Yr, dims, T = cm.load_memmap(fname_new)
    Y = Yr.T.reshape((T,) + dims, order='F')

    # Set up the cluster
    n_processes = setup_cluster(args.processes)

    # Set output
    os.makedirs(args.output_dir, exist_ok=True)

    # Compute correlation and peak-to-noise ratio images
    logging.info("Computing correlation and peak-to-noise ratio images...")
    cn_filter, pnr = cm.summary_images.correlation_pnr(Y, gSig=args.gSig, swap_dim=False)

    # Plot the correlation and peak-to-noise ratio images
    plot_correlations(cn_filter, pnr, args.output_dir)



    # Stop the cluster
    logging.info("Stopping the cluster...")
    cm.stop_server(dview=cluster)

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)