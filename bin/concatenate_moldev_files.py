#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import re
import gc
import logging
import argparse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
## 3rd party
import numpy as np
import tifffile
## package
from load_tiff import load_image_data_moldev_concat


# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Concatenates related TIFF files from MolDev"
epi = """DESCRIPTION:
    The script performs the following steps:
    1. Creates a new directory for storing the combined TIFF files.
    2. Checks if any combined files already exist to avoid reprocessing.
    3. Concatenates the image data from related TIFF files and saves the combined images.
    4. Preserves metadata from the first file in each group during the save process.
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('img_files', type=str, nargs='+',
                    help='Image files')
parser.add_argument('-o', '--output', type=str, default='combined.tif',
                    help='Output image file')
parser.add_argument('--version', action='version', version='0.1.0')

def find_tiff_files(input_dir: str) -> list:
    """
    Recursively find all TIFF files in the input directory
    Args:
        input_dir: Path to the directory containing TIFF files
    Returns:
        List of TIFF file paths
    """
    # recursively find all "*.tif" files
    logging.info(f"Searching for TIFF files in: {input_dir}")
    tif_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.tif'):
                tif_files.append(os.path.join(root, file))
    logging.info(f"  Found {len(tif_files)} TIFF files")
    return tif_files

def group_tiff_files(tif_files: list) -> dict:
    """
    Group related TIFF files by their base name
    Args:
        tif_files: List of TIFF file paths
    Returns:
        Dictionary of related TIFF files grouped by their base name
    """
    # group files by basename
    logging.info("Grouping files by base name")
    file_groups = {}
    pattern = re.compile(r"(.+?)(-file\d+)?\.tif$")
    for filename in tif_files:
        # Match the filename against the pattern
        match = pattern.match(filename)
        if match:
            # Extract the base name and part suffix
            base_name, part_suffix = match.groups()
            # Group files by their base name
            if base_name in file_groups:
                file_groups[base_name].append(filename)
            else:
                file_groups[base_name] = [filename]
    logging.info(f"  Found {len(file_groups)} groups of related files")
    return file_groups

def filter_tiff_files(file_groups: dict, test_image_nums: str, test_image_count: int) -> dict:
    """
    Filter the groups of TIFF files based on the provided test_image_nums or test_image_count
    Args:
        file_groups: Dictionary of related TIFF files grouped by their base name
        test_image_nums: Comma-delimited list of indices to select specific image groups
        test_image_count: Number of randomly selected image groups to process
    Returns:
        Dictionary of filtered TIFF files grouped by their base name
    """
    group_ids = None
    if test_image_count > 0:
        # randomly select N image groups
        logging.info(f"Selecting {test_image_count} random image groups")
        group_ids = np.random.choice(list(file_groups.keys()), test_image_count, replace=False)
    elif test_image_nums is not None:
        # select specific image groups to process
        logging.info("Selecting specific image groups")
        test_image_nums = [int(i) for i in test_image_nums.split(',')]
        group_ids = list(file_groups.keys())
        group_ids = [group_ids[i] for i in test_image_nums if i < len(group_ids)]
    # group files by basename
    if group_ids is not None:
        file_groups = {k: v for k, v in file_groups.items() if k in group_ids}
    return file_groups

def concatenate_images(files: list, output_file: str) -> None:
    """
    Concatenate the image data from related TIFF files and save the combined image
    Args:
        files: List of TIFF file paths
        output_dir: Directory path for storing the combined
    """
    # Status 
    logging.info(f"Concatenating {len(files)} images to: {output_file}")

    # Sort files to ensure they are concatenated in the correct order
    files.sort()

    # Load images and concatenate
    combined_image = np.concatenate([tifffile.imread(f) for f in files], axis=0)  # Change axis if needed for your images
    logging.info(f"  Combined image shape: {combined_image.shape}")

    # Read metadata from the first image
    with tifffile.TiffFile(files[0]) as tif:
        metadata = tif.pages[0].tags

        # Ensure ImageDescription is valid XML
        image_description = metadata.get('ImageDescription', None)
        if image_description:
            try:
                ET.fromstring(image_description.value)
            except ET.ParseError:
                logging.warning(f"Invalid XML in ImageDescription for file {files[0]}. Fixing it.")
                image_description.value = "<MetaData></MetaData>"

        # Remove StripOffsets tag to avoid issues with saving
        metadata = {tag.name: tag.value for tag in metadata.values() if tag.name != 'StripOffsets'}

    # output directory
    output_dir = os.path.dirname(output_file)
    if output_dir != "" and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the combined image with metadata
    with tifffile.TiffWriter(output_file, bigtiff=True) as tif_writer:
        tif_writer.write(combined_image, metadata=metadata)
    logging.info(f"  Saved combined image: {output_file}")

def main(args):
    # Check if the output file already exists
    logging.info("Starting concatenate_moldev_files.py...")
    concatenate_images(args.img_files, args.output)

    # Check the format of the output
    logging.info("Checking the format of the output...")
    gc.collect()
    load_image_data_moldev_concat(args.output)

## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
