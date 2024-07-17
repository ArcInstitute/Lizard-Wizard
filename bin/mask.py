#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import logging
import argparse
import tifffile
## 3rd party
import matplotlib.pyplot as plt
import numpy as np
from cellpose import models, io
## source
from load_czi import load_image_data_czi
from load_tiff import load_image_data_moldev

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Mask image"
epi = """DESCRIPTION:
   
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('img_file', type=str,
                    help='Directory path containing the image files')
parser.add_argument('--file-type', type=str, default='zeiss',
                    help='Type of image file')

# functions
def segment_image(im_min, model, max_diameter):
    """
    Segments the image using the provided model and adjusts the diameter if necessary.
    Switches to an alternate model if initial segmentation fails.

    Parameters:
    - im_min (numpy.ndarray): The minimum projection of the image series.
    - model (Cellpose model): The initial Cellpose model to use for segmentation.
    - max_diameter (int): The maximum allowable diameter for segmentation.

    Returns:
    - masks (numpy.ndarray): The segmentation masks.
    - success (bool): Whether the segmentation was successful.
    """
    diameter = 300
    first_exceed = False
    original_model = model
    while True:
        masks, _, _, _ = model.eval(im_min, diameter=diameter)
        if np.sum(masks) > 0:
            # success?
            return masks, True
        elif diameter > max_diameter:
            if not first_exceed:
                diameter = max_diameter
                first_exceed = True
                logging.warning(f"Diameter exceeded max dimensions. Setting diameter to {max_diameter}.")
            else:
                if model == original_model:
                    logging.info("Switching to 'cyto3' model.")
                    model = models.Cellpose(gpu=False, model_type='cyto3')
                    diameter = 300
                    first_exceed = False
                else:
                    msg = f"Segmentation Failure: Diameter {diameter} exceeds image dimensions {max_diameter}."
                    logging.error(msg)
                    return None, False
        else:
            diameter += 200
            logging.info(f"No object detected. Increasing diameter to {diameter} and retrying...")
    # return failed
    return None, False

def mask_image(im, im_min, img_file) -> np.ndarray:
    """
    """
    logging.info("Masking image...")

    # Import the cellpose model
    model = models.Cellpose(gpu=False, model_type='nuclei')
            
    # Grab the min projection of the image series
    im_min = np.squeeze(np.min(im, axis=1))
    max_diameter = im_min.shape[0]
            
    # Perform segmentation
    masks, success = segment_image(im_min, model, max_diameter)

    # Check if segmentation was successful        
    if not success:
        logging.error(f"Segmentation failed for file {img_file}. Proceeding without creating mask.")

    # Return the masks as a binary array
    return masks

def plot_mask(original_image, masked_image, mask, save_path=None):
    """
    Plots the original projection image, the masked image, and the mask side by side, and saves the figure if a save path is provided.

    Parameters:
    - original_image (np.ndarray): The original min projection image.
    - masked_image (np.ndarray): The masked image.
    - mask (np.ndarray): The mask image.
    - save_path (str, optional): The path where the figure should be saved. Default is None.
    """
    # change logging level
    logging.getLogger().setLevel(logging.WARNING)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    axes[0].imshow(original_image, cmap='gray')
    axes[0].set_title('Original Projection Image')
    axes[0].axis('off')

    axes[1].imshow(np.squeeze(np.max(masked_image, axis=0)), cmap='gray')
    axes[1].set_title('Masked Image')
    axes[1].axis('off')

    axes[2].imshow(mask, cmap='gray')
    axes[2].set_title('Mask')
    axes[2].axis('off')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, format='tiff')
    plt.show()

    # status
    logging.getLogger().setLevel(logging.INFO)
    logging.info(f"Masked image plot saved to {save_path}")

def format_masks(im, im_min, masks: np.ndarray, img_file: str):
    # Ensure mask is binary and broadcast the mask to apply it to each time slice
    masked_im = im * masks.astype(bool)[np.newaxis, :, :]
            
    # Add an epsilon to avoid division by zero
    epsilon = 10
            
    # Preprocess the input data to replace zeros and NaNs
    masked_im = np.nan_to_num(masked_im, nan=epsilon, posinf=epsilon, neginf=epsilon)
    masked_im[masked_im == 0] = epsilon

    # Plot the original and masked images side by side
    outfile = os.path.splitext(img_file)[0] + "_masked-plot.tif"
    plot_mask(im_min, masked_im[0], masks, save_path=outfile)
    # Create a temporary directory with a unique name within the temp dir
    #tmp_tmp_dir = os.path.join(tmp_dir, base_fname + '_' + str(np.random.randint(1e18)))
    #os.makedirs(tmp_tmp_dir, exist_ok=True)
            
    # Generate a unique filename for temporary storage
    #tmp_fname = os.path.join(tmp_tmp_dir, 'memfile_tmp' + str(np.random.randint(1e18)) + '.tif')
            
    # Save the masked image to the temp file
    outfile = os.path.splitext(img_file)[0] + "_masked.tif"
    tifffile.imwrite(outfile, masked_im)
    logging.info(f"Masked image saved to {outfile}")

def main(args):
    # Load the image data
    if args.file_type.lower() == 'moldev':
        # Extract the image data for Molecular Devices
        im, frate = load_image_data_moldev(args.img_file)
    elif args.file_type.lower() == 'zeiss':
        # Extract the image data for Zeiss images
        im, frate = load_image_data_czi(args.img_file)
    else:
        raise ValueError(f"File type not recognized: {args.file_type}")

    # Squeeze the image
    im_min = np.squeeze(np.min(im, axis=1))

    # Mask the image
    masks = mask_image(im, im_min, args.img_file)

    # Format the masks
    format_masks(im, im_min, masks, args.img_file)
    
## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)