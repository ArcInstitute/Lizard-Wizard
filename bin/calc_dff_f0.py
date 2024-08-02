#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import logging
import argparse
## 3rd party
import numpy as np
import tifffile
import matplotlib.pyplot as plt
from tqdm import tqdm
## local
from load_czi import load_image_data_czi
from load_tiff import load_image_data_moldev, load_image_data_moldev_concat
from calc_dff_f0_utils import check_and_load_file, create_montage, convert_f_to_dff_perc, draw_dff_activity

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Calculates delta F/F0 (dF/F0) for a given image file and generates spatial components montages."
epi = """DESCRIPTION:

"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument("cnm_A_file", type=str,
                    help="cnm_A npy file")
parser.add_argument("img_file", type=str,
                    help="Unmasking image file.")
parser.add_argument("img_mask_file", type=str,
                    help="Masked image file. If file ends with '-no-mask.tif' then no mask is used.")
parser.add_argument("-f", "--file-type", type=str, default='zeiss',
                    choices = ['moldev', 'zeiss'], 
                    help="Input file type")
parser.add_argument("-t", "--threshold-percentile", type=float, default=0.75,
                    help="Threshold percentile for image processing")


# functions
def read_img_file(img_file: str, file_type: str) -> tuple:
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

    return im, frate, im_shape, im_sz, im_avg

def main(args):
    # Read the image file and get various parameters
    im, frate, im_shape, im_sz, im_avg = read_img_file(args.img_file, args.file_type)

    # check if the mask file is provided
    masks = check_and_load_file(args.img_mask_file)

    # calc the background intensity
    if masks is not None:
        mask_bg = (masks < 1) & (im_avg > 0)
        im_bg = np.median(im_avg[mask_bg]) * 0.9
    else:
        im_bg = np.median(im_avg) * 0.9
    logging.info(f'im_bg estimated as {im_bg}')

    # Load additional data (matrix A)
    A = check_and_load_file(args.cnm_A_file)

    # Initialize storage for processed images
    im_st = np.zeros((A.shape[1], im_sz[0], im_sz[1]), dtype='uint16')
    p_th = args.threshold_percentile
    logging.info('Generating im_st with p_th of {p_th}')
    dict_mask = {}
    
    # Generate im_st by thresholding the components in A
    for i in range(A.shape[1]):
        Ai = np.copy(A[:, i])
        Ai = Ai[Ai > 0]
        thr = np.percentile(Ai, p_th)
        imt = np.reshape(A[:, i], im_sz, order='F')
        im_thr = np.copy(imt)
        im_thr[im_thr < thr] = 0
        im_thr[im_thr >= thr] = i + 1
        im_st[i, :, :] = im_thr
        dict_mask[i] = im_thr > 0

    # Calculate the grid shape
    n_images = len(im_st)
    grid_shape = (np.ceil(np.sqrt(n_images)).astype(int), np.ceil(np.sqrt(n_images)).astype(int))
    
    # Create the montage for all components
    montage_image = create_montage(im_st, im_avg, grid_shape)    


## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)



