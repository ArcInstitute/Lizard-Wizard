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
from scipy.ndimage import label, sum as ndi_sum
from cellpose import models, io
## source
from load_czi import load_image_data_czi
from load_tiff import load_image_data_moldev_concat

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Mask image"
epi = """DESCRIPTION:
Mask the image using the Cellpose model.
If masking fails, the unmasking image is outputted.
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('img_file', type=str,
                    help='Directory path containing the image files')
parser.add_argument('--file-type', type=str, default='zeiss',
                    help='Type of image file')
parser.add_argument('--use-2d', action='store_true',
                    help='2d, so no masking')
parser.add_argument('--min-object-size', type=int, default=500,
                    help='Minimum size of objects in pixels for successful segmentation')
parser.add_argument('--max-segment-retries', type=int, default=3,
                    help='Maximum number of retries for segmentation if objects are below the threshold')
parser.add_argument('--start-diameter', type=int, default=300,
                    help='Starting diameter for segmentation')
parser.add_argument('--diameter-step', type=int, default=200,
                    help='Step to increase the diameter after each failed attempt')


# functions
def segment_image(im_min: np.ndarray, model: models.Cellpose, max_diameter: int, start_diameter: int = 300, diameter_step: int = 200) -> tuple:
    """
    Segments the image using the provided model and adjusts the diameter if necessary.
    Switches to an alternate model if initial segmentation fails.
    Args:
        im_min: The minimum projection of the image series.
        model: The initial Cellpose model to use for segmentation.
        max_diameter: The maximum allowable diameter for segmentation.
        start_diameter: The starting diameter for segmentation. Default is 300.
        diameter_step: The step to increase the diameter after each failed attempt. Default is 200.

    Returns:
        tuple containing:
        - masks (numpy.ndarray): The segmentation masks.
        - success (bool): Whether the segmentation was successful.
    """
    diameter = start_diameter
    first_exceed = False
    original_model = model

    while diameter <= max_diameter or not first_exceed:
        masks, _, _, _ = model.eval(im_min, diameter=diameter)
        if np.sum(masks) > 0:
            logging.info(f"Segmentation succeeded with diameter {diameter}.")
            return masks, True, diameter
        
        elif diameter > max_diameter:
            if not first_exceed:
                diameter = max_diameter
                first_exceed = True
                logging.warning(f"Diameter exceeded max dimensions. Setting diameter to {max_diameter}.")
            else:
                if model == original_model:
                    logging.info("Switching to 'cyto3' model.")
                    model = models.Cellpose(gpu=False, model_type="cyto3")
                    diameter = start_diameter
                    first_exceed = False
                else:
                    msg = f"Segmentation Failure: Diameter {diameter} exceeds image dimensions {max_diameter}."
                    logging.warning(msg)
                    return None, False, diameter
        else:
            diameter += diameter_step
            logging.info(f"No object detected. Increasing diameter to {diameter} and retrying...")
    # failed to segment
    return None, False, diameter

def mask_image(im_min: np.ndarray, min_object_size: int=500, max_segment_retries: int=3, start_diameter: int = 300, diameter_step: int = 200) -> np.ndarray:
    """
    Masks the image using the Cellpose model.
    Args:
        im_min: The minimum projection of the image data.
        min_object_size: The minimum object size to consider for successful segmentation. Default is 1000.
        max_retries: The maximum number of retries to attempt segmentation. Default is 3.
        start_diameter: The starting diameter for segmentation. Default is 300.
        diameter_step: The step to increase the diameter after each failed attempt. Default is 200.

    Returns:
        masks: The masks to apply to the image data. Returns None if segmentation fails.
    """
    logging.info("Masking image...")

    # Import the cellpose model
    model = models.Cellpose(gpu=False, model_type="nuclei")

    # Set the maximum diameter for segmentation
    max_diameter = im_min.shape[0]

    if start_diameter > max_diameter:
        logging.error("Start_diameter cannot exceed max_diameter. Setting start_diameter to max_diameter.")
        start_diameter = max_diameter
            
    # Perform segmentation
    masks, success, final_diameter = segment_image(im_min, model, max_diameter, start_diameter)

    # Check if segmentation was successful        
    if not success:
        logging.error(f"Segmentation failed. Proceeding without creating mask.")
        return None

    # Detect object sizes
    object_sizes = detect_object_sizes(masks)
    logging.info(f"Object sizes detected: {object_sizes}")

    # Check if all objects are larger than the threshold
    retry_count = 0
    while retry_count < max_segment_retries:
        valid_sizes = [size for size in object_sizes if size is not None]

        if all(size < min_object_size for size in valid_sizes):
            logging.warning(f"All objects are smaller than the threshold ({min_object_size}). Retrying segmentation attempt #{retry_count + 1}...")
        
            if final_diameter >= max_diameter:
                logging.warning(f"Diameter exceeded max dimensions. Resetting to {max_diameter}.")
                final_diameter = max_diameter
            else:
                final_diameter += diameter_step
                logging.info(f"Increasing diameter to {final_diameter} for retry #{retry_count + 1}...")

            # Perform segmentation
            masks, success, final_diameter = segment_image(im_min, model, max_diameter, start_diameter=final_diameter)
            
            # Check if segmentation was successful by detecting object sizes
            object_sizes = detect_object_sizes(masks)
            logging.info(f"Object sizes detected: {object_sizes} for retry #{retry_count + 1}")
        else:
            break  # Exit if valid objects are detected

        # Increment the retry count
        retry_count += 1

    # Log the success message after exiting the loop
    if any(size >= min_object_size for size in valid_sizes):
        logging.info(f"Successfully segmented objects larger than the threshold ({min_object_size}) after {retry_count} attempts.")
    else:
        logging.error(f"Segmentation failed after {retry_count} retries. No objects met the threshold ({min_object_size}). Proceeding without creating mask.")
        return None

    # Return the masks as a binary array
    return masks

def create_minprojection(im: np.ndarray, img_file: str, file_type: str) -> np.ndarray:
    """
    Create a min projection of the image series and save it as a tiff file.
    Args:
        im: The image data.
        img_file: The path to the image file.
        file_type: The type of file being processed.
    Returns:
        im_min: The min projection of the image series.
    """
    # Grab the min projection of the image series
    if file_type.lower() == "moldev":
        im_min = np.min(im, axis=0)
    else:
        im_min = np.squeeze(np.min(im, axis=1))

    # Save the min projection image
    base_fname = os.path.splitext(os.path.basename(img_file))[0]
    tifffile.imwrite(f"{base_fname}_minprojection.tif", im_min)
    # return the min projection
    return im_min

def plot_mask(original_image: np.ndarray, masked_image: np.ndarray, mask: np.ndarray, 
              file_type: str, save_path: str=None) -> None:
    """
    Plots the original projection image, the masked image, and the mask side by side,
    and saves the figure if a save path is provided.
    Args:
        original_image: The original min projection image.
        masked_image: The masked image.
        mask: The mask image.
        file_type: The type of file being processed.
        save_path: The path where the figure should be saved. Default is None.
    """
    # Change logging level
    logging.getLogger().setLevel(logging.WARNING)

    # Plot the original and masked images side by side
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    if file_type == 'zeiss':
        axes[1].imshow(np.squeeze(np.max(masked_image, axis=0)), cmap='gray')
    else:
        axes[1].imshow(masked_image, cmap='gray')
    
    axes[0].imshow(original_image, cmap='gray')
    axes[0].set_title('Original Projection Image')
    axes[0].axis('off')

    axes[1].set_title('Masked Image')
    axes[1].axis('off')

    axes[2].imshow(mask, cmap='gray')
    axes[2].set_title('Mask')
    axes[2].axis('off')

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, format='tiff')
    plt.show()

    # Status
    logging.getLogger().setLevel(logging.INFO)
    logging.info(f"Masked image plot saved to {save_path}")

def format_masks(im: np.ndarray, im_min: np.ndarray, masks: np.ndarray, 
                 img_file: str, file_type: str) -> None:
    """
    Formats the masks to apply to each time slice of the image, and saves the masked image and the masks to tiff files.
    Args:
        im: The original image data.
        im_min: The minimum projection of the image data.
        masks: The masks to apply to the image data.
        img_file: The path to the image file.
        file_type: The type of file being processed.
    """
    # Get the base file name
    base_fname = os.path.splitext(os.path.basename(args.img_file))[0]

    # Write masks to tiff file
    tifffile.imwrite(f"{base_fname}_masks.tif", masks)

    # Ensure mask is binary and broadcast the mask to apply it to each time slice
    masked_im = im * masks.astype(bool)[np.newaxis, :, :]
            
    # Add an epsilon to avoid division by zero
    epsilon = 10
            
    # Preprocess the input data to replace zeros and NaNs
    masked_im = np.nan_to_num(masked_im, nan=epsilon, posinf=epsilon, neginf=epsilon)
    masked_im[masked_im == 0] = epsilon

    # Validate and preprocess the masked data
    logging.info("Validating masked image data...")
    masked_im = validate_input_data(masked_im, f"{base_fname}_masked")

    # Plot the original and masked images side by side
    outfile = os.path.splitext(img_file)[0] + "_masked-plot.tif"
    plot_mask(im_min, masked_im[0], masks, file_type=file_type, save_path=outfile)
            
    # Save the masked image to the temp file
    outfile = os.path.splitext(img_file)[0] + "_masked.tif"
    tifffile.imwrite(outfile, masked_im)
    logging.info(f"Masked image saved to {outfile}")

def detect_object_sizes(mask: np.ndarray) -> list:
    """
    Detects the sizes of objects in the given mask.
    Args:
        mask: Binary mask where objects are labeled as 1.
    Returns:
        A list of object sizes (number of pixels per object).
    """
    if mask is None or mask.sum() == 0:
        logging.warning("Mask is empty. No objects detected.")
        return []

    labeled_mask, num_features = label(mask)
    object_sizes = [ndi_sum(mask, labeled_mask, index=i + 1) for i in range(num_features)]
    return object_sizes

def validate_input_data(Y: np.ndarray, fname: str, 
                        epsilon: float = np.finfo(float).eps) -> np.ndarray:
    """
    Validates and preprocesses input data for further processing.
    
    Args:
        Y: Input data array
        fname: Filename for logging purposes
        epsilon: Small value to replace zeros/invalid values. If None, calculated from data
    
    Returns:
        Preprocessed numpy array with validated data
        
    Raises:
        ValueError: If validation completely fails
    """
    # Check for empty or invalid data
    if Y is None or Y.size == 0:
        logging.error(f"Empty or invalid data in {fname}")

    # Calculate epsilon if not provided
    if epsilon is None:
        epsilon = np.finfo(Y.dtype).eps * 10

    valid_mask = ~np.isnan(Y) & ~np.isinf(Y)
    n_invalid = Y.size - np.sum(valid_mask)

    # Log basic statistics about input data
    logging.info("Input data statistics for debugging:")
    logging.info(f"Shape: {Y.shape} ({Y.shape[0]} time points)")
    logging.info(f"dtype: {Y.dtype}")
    logging.info(f"Min: {np.min(Y)}")
    logging.info(f"Max: {np.max(Y)}")
    logging.info(f"Mean: {np.mean(Y)}")
    logging.info(f"Median: {np.median(Y)}")
    logging.info(f"Contains NaN: {np.any(np.isnan(Y))}")
    logging.info(f"Contains inf: {np.any(np.isinf(Y))}")
    logging.info(f"Contains zeros: {np.any(Y == 0)}")
    
    # Save original data statistics
    orig_min = np.min(Y[valid_mask])
    orig_max = np.max(Y[valid_mask])
    
    # Handle invalid values
    if np.any(np.isnan(Y)) or np.any(np.isinf(Y)):
        logging.warning(f"Found NaN/inf values in {fname}, replacing with valid values")
        Y = np.nan_to_num(Y, nan=epsilon, posinf=orig_max, neginf=orig_min)
    
    # Handle zeros or very small values that could cause division issues
    if np.any(Y < epsilon):
        logging.warning(f"Found values smaller than {epsilon} in {fname}, replacing with epsilon")
        Y[Y < epsilon] = epsilon
    
    # Verify the fixes worked
    if np.any(np.isnan(Y)) or np.any(np.isinf(Y)):
        logging.error(f"Failed to fix NaN/inf values in {fname}")
    
    # Log final statistics
    logging.info("Final data statistics after preprocessing:")
    logging.info(f"Min: {np.min(Y)}")
    logging.info(f"Max: {np.max(Y)}")
    logging.info(f"Mean: {np.mean(Y)}")
    
    return Y


def main(args):
    logging.info("Starting mask.py...")
    # Set up the cellpose logger
    logger = io.logger_setup()

    # Load the image data
    if args.file_type.lower() == "moldev":
        # Extract the image data for Molecular Devices
        im, frate = load_image_data_moldev_concat(args.img_file)
    elif args.file_type.lower() == "zeiss":
        # Extract the image data for Zeiss images
        im, frate = load_image_data_czi(args.img_file)
    else:
        raise ValueError(f"File type not recognized: {args.file_type}")

    # Write frame rate to a file
    logging.info(f"Frame rate: {frate}")
    with open("frate.txt", "w") as outF:
        outF.write(f"FRATE={frate}")
    
    # Create min projection
    im_min = create_minprojection(im, args.img_file, args.file_type)

    # Save the image as a tif file, if no masking
    if args.use_2d:
        logging.info("2D image, skipping masking")
        # masked image
        outfile = os.path.splitext(args.img_file)[0] + "_no-masked.tif"
        tifffile.imwrite(outfile, im)
        logging.info(f"No-masked image saved to {outfile}")
        # image masks
        outfile = os.path.splitext(args.img_file)[0] + "_no-masks.tif"
        open(outfile, "w").close()
        logging.info(f"No-masks image saved to {outfile}")
        exit(0)

    # Mask the image
    masks = mask_image(im_min, args.min_object_size, args.max_segment_retries, args.start_diameter, args.diameter_step)

    # If segmentation/masking fails, write unmasked image
    if masks is None:
        logging.warning("Masking failed; writing the unmasked image")
        # masked image
        outfile = os.path.splitext(args.img_file)[0] + "_no-masked.tif"  
        tifffile.imwrite(outfile, im)
        logging.info(f"No-masked image saved to {outfile}")
        # image masks
        outfile = os.path.splitext(args.img_file)[0] + "_no-masks.tif"
        open(outfile, "w").close()
        logging.info(f"No-masks image saved to {outfile}")
        exit(0)

    # Format the masks
    format_masks(im, im_min, masks, args.img_file, args.file_type)
    
## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)