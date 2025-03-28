#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import logging
import argparse
from typing import Tuple
## 3rd party
import numpy as np
import tifffile
import matplotlib.pyplot as plt
from tqdm import tqdm
## local
from load_czi import load_image_data_czi
from load_tiff import load_image_data_moldev, load_image_data_moldev_concat
from calc_dff_f0_utils import (
    check_and_load_file, calc_mean_signal, create_montage, convert_f_to_dff_perc, draw_dff_activity, 
    plot_montage, define_slice_extraction, save_dff_dat
)

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Calculate the delta F/F0"
epi = """DESCRIPTION:
Calculates delta F/F0 (dF/F0) for a given image file and generates spatial components montages.
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument("cnm_A_file", type=str,
                    help="cnm_A npy file")
parser.add_argument("cnm_idx_file", type=str,
                    help="cnm_idx npy file")
parser.add_argument("img_file", type=str,
                    help="Unmasking image file.")
parser.add_argument("img_masks_file", type=str,
                    help="Image masks. If file ends with '_no-masks.tif' then no mask is used.")
parser.add_argument("-o", "--output-dir", type=str, default='output',
                    help="Output directory")
parser.add_argument("-f", "--file-type", type=str, default='zeiss',
                    choices = ['moldev', 'zeiss'], 
                    help="Input file type")
parser.add_argument('--p_th', type=float, default=0.75,
                    help='Threshold percentile for image processing')
parser.add_argument('--f_baseline_perc', type=float, default=8,
                    help='Percentile value for the filter when converting fluorescence data to delta F/F')
parser.add_argument('--win_sz', type=int, default=500,
                    help='Window size for the percent filter.')

# functions
def read_img_file(img_file: str, file_type: str) -> Tuple[np.ndarray, float, tuple, list, np.ndarray]:
    """
    Read the image file and return the image data, frame rate, image shape, image size and average image.
    Args:
        img_file: path to the image file
        file_type: type of the image file
    Returns:
        tuple of image data
        - im: image data
        - frate: frame rate
        - im_shape: image shape
        - im_sz: image size
        - im_avg: average image
    """
    # Load the image data
    if file_type.lower() == 'moldev' and img_file.endswith('_full.tif'):
        # Load the concatenated tiff file
        im, frate = load_image_data_moldev_concat(img_file)
    elif file_type.lower() == 'moldev':
        # Extract the image data if from moldev instrument
        im, frate = load_image_data_moldev(img_file)
    elif file_type.lower() == 'zeiss':
        # Extract the image data if czi file form zeiss instrument
        im, frate = load_image_data_czi(img_file)
    else:
        raise ValueError(f"Unknown file type: {file_type}")
        
    # Get the image shape and size
    im_shape = im.shape
    if file_type.lower() == 'moldev':
        im_sz = [im_shape[1], im_shape[2]]
        im_avg = np.mean(im, axis=0)
    elif file_type.lower() == 'zeiss':
        im_sz = [im_shape[3], im_shape[4]]
        im_avg = np.squeeze(np.mean(im, axis=1))
    else:
        raise ValueError(f"Unknown file type: {file_type}")

    # stats
    logging.info(f"Frame rate: {frate}")
    logging.info(f"Image shape: {im_shape}")
    logging.info(f"Image size: {im_sz}")
    return im, float(frate), im_shape, im_sz, im_avg

def main(args):
    logging.info("Starting calc_dff_f0.py...")
    # output 
    ## basename
    base_fname = os.path.splitext(os.path.basename(args.img_file))[0]
    ## directory
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)
    ## file names
    outfile_montage = os.path.join(args.output_dir, base_fname + "_montage.png")
    outfile_montage_filtered = os.path.join(args.output_dir, base_fname + "_montage-filtered.png")
    outfile_im_st = os.path.join(args.output_dir, base_fname + "_im-st.tif")

    # Read the image file and get various parameters
    logging.info(f"Reading image file: {args.img_file}")
    im, frate, im_shape, im_sz, im_avg = read_img_file(args.img_file, args.file_type)

    # Check if the mask file is provided
    logging.info(f"Reading image masks file: {args.img_masks_file}")
    masks = check_and_load_file(args.img_masks_file)

    # Calc the background intensity
    if masks is not None:
        logging.info(f"  Masks shape: {masks.shape}")
        mask_bg = (masks < 1) & (im_avg > 0)
        im_bg = np.median(im_avg[mask_bg]) * 0.9
    else:
        logging.warning("  No masks provided. Estimating background intensity from the average image.")
        im_bg = np.median(im_avg) * 0.9
    logging.info(f"im_bg estimated as {im_bg}")

    # Load additional data (matrix A)
    logging.info(f"Reading matrix A file: {args.cnm_A_file}")
    A = check_and_load_file(args.cnm_A_file)
    logging.info(f"  Matrix A shape: {A.shape}")

    # Check whether A is blank
    if A.shape[1] == 0:
        logging.error("Matrix A is blank. Writing out blank files and exiting...")
        open(outfile_montage, "w").close()
        open(outfile_montage_filtered, "w").close()
        open(outfile_im_st, "w").close()
        exit()

    # Initialize storage for processed images
    im_st = np.zeros((A.shape[1], im_sz[0], im_sz[1]), dtype='uint16')
    logging.info(f"Generating im_st with p_th of {args.p_th}")
    dict_mask = {}
    
    # Generate im_st by thresholding the components in A
    for i in range(A.shape[1]):
        Ai = np.copy(A[:, i])
        Ai = Ai[Ai > 0]
        thr = np.percentile(Ai, args.p_th)
        imt = np.reshape(A[:, i], im_sz, order='F')
        im_thr = np.copy(imt)
        im_thr[im_thr < thr] = 0
        im_thr[im_thr >= thr] = i + 1
        im_st[i, :, :] = im_thr
        dict_mask[i] = im_thr > 0

    # Save the generated im_st image
    tifffile.imwrite(outfile_im_st, im_st)

    # Calculate the grid shape
    n_images = len(im_st)
    grid_shape = (np.ceil(np.sqrt(n_images)).astype(int), np.ceil(np.sqrt(n_images)).astype(int))
    
    # Create the montage for all components
    logging.info("Creating montage image...")
    montage_image = create_montage(im_st, im_avg, grid_shape)
    plot_montage(montage_image, outfile_montage)
    
    # Filtered components montage
    ## Load index of accepted components from previous filtering step
    logging.info(f"Reading index file: {args.cnm_idx_file}")
    idx = np.load(args.cnm_idx_file)
    logging.info(f"Loaded index array: {idx}, shape: {idx.shape}")

    if idx.size == 0:
        logging.warning("Index file is empty. No components to filter.")
    else:
        ## Filter the components
        logging.info("Filtering montage components...")
        filtered_im_st = im_st[idx, :, :]
        
        if filtered_im_st.size == 0:
            logging.error("Filtered component image stack is empty. Skipping montage creation.")
        else:
            n_images = len(filtered_im_st)
            grid_shape = (np.ceil(np.sqrt(n_images)).astype(int), np.ceil(np.sqrt(n_images)).astype(int))
            ### Create the montage for all components
            logging.info("Creating montage image...")
            montage_image = create_montage(filtered_im_st, im_avg, grid_shape)
            plot_montage(montage_image, outfile_montage_filtered)

    # Define the slice extraction logic based on file type
    f_dat, slice_indices, slice_extraction = define_slice_extraction(
        args.file_type, A, im, im_shape, im_bg
    )

    # Process each z-slice of the image to compute mean fluorescence
    f_dat = calc_mean_signal(
        im=im, 
        slice_indices = slice_indices, 
        slice_extraction = slice_extraction, 
        A = A, 
        dict_mask = dict_mask,
        im_bg = im_bg, 
        f_dat = f_dat, 
        fname = base_fname
    )
    
    # Convert fluorescence data to delta F/F
    dff_dat = convert_f_to_dff_perc(f_dat, perc=args.f_baseline_perc, win_sz=args.win_sz)
    
    # Save dff_dat data
    save_dff_dat(f_dat, dff_dat, base_fname, args.output_dir)

    # Draw only accepted df/f0 values
    draw_dff_activity(
        dff_dat, idx, 
        max_dff_int=0.45,
        begin_tp=0, 
        end_tp=-1, 
        output_dir=args.output_dir, 
        base_fname=base_fname,
        dff_bar=1,
        frate=frate, 
        n_start=0, 
        n_stop=-1, 
        lw=0.55, 
        sz_per_neuron=0.5
    )

## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)



