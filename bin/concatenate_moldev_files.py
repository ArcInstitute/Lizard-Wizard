#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import re
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
## 3rd party
import numpy as np
import tifffile

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = 'Concatenates related TIFF files from MolDev '
epi = """DESCRIPTION:
    The script performs the following steps:
    1. Groups related TIFF files based on their base names.
    2. Creates a new directory for storing the combined TIFF files.
    3. Checks if any combined files already exist to avoid reprocessing.
    4. Concatenates the image data from related TIFF files and saves the combined images.
    5. Preserves metadata from the first file in each group during the save process.
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('input_dir', type=str,
                    help='Directory path containing the image files')
parser.add_argument('--output-dir', type=str, default="tiff_combined",
                    help='Directory path for storing the combined image files')
parser.add_argument('--test-image-nums', type=str, default=None,
                    help='Which images to process (comma-delim list of indices)')
parser.add_argument('--test-image-count', type=int, default=0,
                    help='Number of randomly selected images to process')
parser.add_argument('-t', '--threads', type=int, default=2,
                    help='Number of threads to use')
parser.add_argument('--version', action='version', version='0.1.0')

def find_tiff_files(input_dir):
    # recursively find all "*.tif" files
    logging.info(f"Searching for TIFF files in: {input_dir}")
    tif_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.tif'):
                tif_files.append(os.path.join(root, file))
    logging.info(f"  Found {len(tif_files)} TIFF files")
    return tif_files

def group_tiff_files(tif_files):
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

def filter_tiff_files(file_groups, test_image_nums, test_image_count):
    group_ids = None
    if test_image_nums is not None:
        # select specific image groups to process
        logging.info("Selecting specific image groups")
        test_image_nums = [int(i) for i in test_image_nums.split(',')]
        group_ids = list(file_groups.keys())[test_image_nums]
    elif test_image_count > 0:
        # randomly select N image groups
        logging.info(f"Selecting {test_image_count} random image groups")
        group_ids = np.random.choice(list(file_groups.keys()), test_image_count, replace=False)
    if group_ids is not None:
        file_groups = {k: v for k, v in file_groups.items() if k in group_ids}
    return file_groups

def concatenate_images(base_name, files, output_dir):
    base_name = os.path.basename(base_name)
    logging.info(f"Concatenating related files for {base_name}")
    
    # Name of the combined file to be saved
    combined_filename = f"{base_name}_full.tif"
    combined_file_path = os.path.join(output_dir, combined_filename)
    
    # Sort files to ensure they are concatenated in the correct order
    files.sort()

    # Load images and concatenate
    images = [tifffile.imread(f) for f in files]
    combined_image = np.concatenate(images, axis=0)  # Change axis if needed for your images
    logging.info(f"  Combined image shape: {combined_image.shape}")

    # Read metadata from the first image
    with tifffile.TiffFile(files[0]) as tif:
        metadata = tif.pages[0].tags
    # Remove StripOffsets tag to avoid issues with saving
    metadata = {tag.name: tag.value for tag in metadata.values() if tag.name != 'StripOffsets'}

    # Save the combined image with metadata
    with tifffile.TiffWriter(combined_file_path, bigtiff=True) as tif_writer:
        tif_writer.write(combined_image, metadata=metadata)
    logging.info(f"  Saved combined image: {combined_file_path}")

def main(args):
    # Find all TIFF files in the input directory
    tif_files = find_tiff_files(args.input_dir)

    # Group files by their base name
    file_groups = group_tiff_files(tif_files)
    
    # filtering images by group
    file_groups = filter_tiff_files(file_groups, args.test_image_nums, args.test_image_count)

    # Create a new directory for combined files
    os.makedirs(args.output_dir, exist_ok=True)

    # Concat each group of files
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        # Submit each group of files to the executor
        future_to_base_name = {executor.submit(concatenate_images, base_name, files, args.output_dir): base_name for base_name, files in file_groups.items()}
        # Loop through futures as they complete
        for future in as_completed(future_to_base_name):
            base_name = future_to_base_name[future]
            try:
                future.result()
            except Exception as exc:
                logging.error(f"{base_name} generated an exception: {exc}")
            else:
                logging.info(f"{base_name} processed successfully")

## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)