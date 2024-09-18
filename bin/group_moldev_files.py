#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import re
import gc
import sys
import logging
import argparse
import xml.etree.ElementTree as ET
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

desc = "Concatenates related TIFF files from MolDev"
epi = """DESCRIPTION:
    The script performs the following steps:
    1. Groups related TIFF files based on their base names.
    2. Optionally filters the groups based on the provided test_image_nums or test_image_count.
    3. Creates a csv file with the file groups.
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('input_dir', type=str, 
                    help='Path to the directory containing TIFF files')
parser.add_argument('--output', type=str, default="combined.tif",
                    help='Output file name')
parser.add_argument('--test-image-names', type=str, default=None,
                   help='Which images to process (comma-delim list of file basenames)')
parser.add_argument('--test-image-count', type=int, default=0,
                   help='Number of randomly selected images to process')
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
    # raise an error if no files were found
    if len(tif_files) == 0:
        raise ValueError(f"No TIFF files found in {input_dir}")
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
    # Group files by basename
    logging.info("Grouping files by base name")
    file_groups = {}
    pattern = re.compile(r"(.+?)(-file\d+)?\.tif$")
    for filename in tif_files:
        # Match the filename against the pattern
        match = pattern.match(os.path.basename(filename))
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

def filter_tiff_files(file_groups: dict, test_image_names: str, test_image_count: int) -> dict:
    """
    Filter the groups of TIFF files based on the provided test_image_names or test_image_count
    Args:
        file_groups: Dictionary of related TIFF files grouped by their base name
        test_image_names: Comma-delimited list of file basenames to select specific image groups
        test_image_count: Number of randomly selected image groups to process
    Returns:
        Dictionary of filtered TIFF files grouped by their base name
    """
    group_ids = None
    if test_image_count > 0:
        # randomly select N image groups
        logging.info(f"Selecting {test_image_count} random image groups")
        if test_image_count > len(file_groups):
            raise ValueError("test_image_count is greater than the number of image groups")
        group_ids = np.random.choice(list(file_groups.keys()), test_image_count, replace=False)
    elif test_image_names is not None:
        # select specific image groups to process
        logging.info("Selecting specific image groups")
        test_image_names = [str(x).strip() for x in test_image_names.split(',')]
        group_ids = [x for x in file_groups.keys() if x in test_image_names]
        if len(group_ids) == 0:
            raise ValueError("No matching image groups found")
    # group files by basename
    if group_ids is not None:
        file_groups = {k: v for k, v in file_groups.items() if k in group_ids}
    return file_groups

def validate_group_names(group_names: list):
    regex = re.compile(r"^.+_[A-Z][0-9]{2}_s[0-9]_FITC$")
    all_valid = True
    for group_name in group_names:
        if not regex.match(group_name):
            print(f"Invalid group name: {group_name}", file=sys.stderr)
            all_valid = False
    if not all_valid:
        raise ValueError("Invalid group names found")

def main(args):
    # Find all TIFF files in the input directory
    tif_files = find_tiff_files(args.input_dir)

    # Group files by their base name
    file_groups = group_tiff_files(tif_files)
    
    # Filter images by group
    file_groups = filter_tiff_files(
        file_groups, args.test_image_names, args.test_image_count
    )

    # Validate group names
    validate_group_names(list(file_groups.keys()))

    # Print the groups as csv
    print("group_name,file_path")
    for group_name, files in file_groups.items():
        for file_path in files:
            print(f"{group_name},{file_path}")

## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)