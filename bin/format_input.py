#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import re
import logging
import argparse
## 3rd party
import numpy as np

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Format input files"
epi = """DESCRIPTION:
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('input_dir', type=str,
                    help='Input directory')
parser.add_argument('--output_dir', type=str, default="FMT_OUTPUT",
                    help='Output directory')
parser.add_argument('--file-type', type=str, default="moldev",
                    choices=["moldev", "zeiss"],
                    help='Type of input files')
parser.add_argument('--test-image-names', type=str, default=None,
                   help='Which images to process (comma-delim list of file basenames)')
parser.add_argument('--test-image-count', type=int, default=0,
                   help='Number of randomly selected images to process')

# functions
def find_image_files(input_dir: str) -> list:
    """
    Recursively find all TIFF and CZI files in the input directory
    Args:
        input_dir: Path to the directory containing the image files
    Returns:
        List of image file paths
    """
    # recursively find all image files files
    logging.info(f"Searching for image files in: {input_dir}")
    img_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.tif') or file.endswith('.tiff') or file.endswith('.czi'):
                file_path = os.path.join(root, file)
                img_files.append(os.path.abspath(file_path))
    # raise an error if no files were found
    if len(img_files) == 0:
        raise ValueError(f"No image files found in {input_dir}")
    logging.info(f"  Found {len(img_files)} image files")
    return img_files

def filter_img_files(img_files: list, file_type: str) -> list:
    """
    Filter image files by file type.
    Args:
        img_files: List of image file paths
        file_type: Type of image files to filter by
    Returns:
        List of filtered image file
    """
    # filter image files by file type
    filtered_files = []
    for file in img_files:
        if file_type == "moldev":
            if file.endswith('.tif') or file.endswith('.tiff'):
                filtered_files.append(file)
        elif file_type == "zeiss":
            if file.endswith('.czi'):
                filtered_files.append(file)
    if len(filtered_files) == 0:
        ext = "tiff or tif" if file_type == "moldev" else "czi"
        raise ValueError(f"No {ext} files found in {input_dir}")
    logging.info(f"  Filtered to {len(filtered_files)} image files")
    return filtered_files

def group_img_files(img_files: list) -> dict:
    """
    Group related img files by their base name
    Args:
        img_files: List of img file paths
    Returns:
        Dictionary of related img files grouped by their base name
    """
    # Group files by basename
    logging.info("Grouping files by base name")
    file_groups = {}
    pattern = re.compile(r"(.+?)(-file\d+)?\.(tif|tiff|czi)$")
    for file_path in img_files:
        # Match the file_path against the pattern
        match = pattern.match(os.path.basename(file_path))
        if match:
            # Extract the base name and part suffix
            base_name, part_suffix, _ = match.groups()
            # Group files by their base name
            if base_name in file_groups:
                file_groups[base_name].append(file_path)
            else:
                file_groups[base_name] = [file_path]
    logging.info(f"  Found {len(file_groups)} groups of related files")
    return file_groups

def select_img_groups(file_groups: dict, test_image_names: str, test_image_count: int) -> dict:
    """
    Select the groups of image files based on the provided test_image_names or test_image_count
    Args:
        file_groups: Dictionary of files grouped by their base name
        test_image_names: Comma-delimited list of file basenames to select specific image groups
        test_image_count: Number of randomly selected image groups to process
    Returns:
        Dictionary of filtered image files grouped by their base name
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
        logging.info("Selecting specific image groups based on --test-image-names")
        test_image_names = [str(x).strip() for x in test_image_names.split(',')]
        group_ids = [x for x in file_groups.keys() if x in test_image_names]
        if len(group_ids) == 0:
            file_groups_str = ', '.join(file_groups.keys())
            raise ValueError(f"No matching image groups found. Available groups: {file_groups_str}")
    # group files by basename
    if group_ids is not None:
        file_groups = {k: v for k, v in file_groups.items() if k in group_ids}
    return file_groups

def create_symlinks(img_groups: dict, output_dir: str) -> dict:
    """
    Create symlinks to the image files in the output directory.
    Args:
        img_groups: Dict of image groups
        output_dir: Path to the output directory
    Returns:
        Updated dict of image groups with the full path to the symlinked files
    """
    # create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    # regex to remove special characters for output file names
    regex = re.compile(r'[^a-zA-Z0-9._-]')
    regex2 = re.compile(r'[^a-zA-Z0-9]+$')
    # create symlinks
    updated_groups = {}
    for group,file_paths in img_groups.items():
        for file_path in file_paths:
            # get the output file name
            file_name = os.path.basename(file_path)
            output_path,ext = os.path.splitext(regex.sub('_', file_name))
            output_path = regex2.sub('', output_path) + ext
            output_path = os.path.join(output_dir, output_path)
            # create symlink
            if os.path.exists(output_path):
                logging.warning(f"File {output_path} already exists")
            else:
                os.symlink(file_path, output_path)
                logging.info(f"Created symlink: {output_path}")
            # update the group with the symlink path
            output_path = os.path.abspath(output_path)
            if group in updated_groups:
                updated_groups[group].append(output_path)
            else:
                updated_groups[group] = [output_path]
    return updated_groups

def write_group_table(img_groups: list, outfile: str="groups.csv") -> None:
    """
    Write group table.
    Args:
        img_groups: List of image groups
        output_dir: Path to the output directory
    """
    # write table
    regex = re.compile(r'[^a-zA-Z0-9._-]')
    with open(outfile, "w") as file:
        file.write("group_name,file_path\n")
        for group, img_files in img_groups.items():
            group_str = regex.sub('_', group)
            for img_file in img_files:
                file.write(f"{group_str},{img_file}\n")
    # status
    logging.info(f"Group table written to: {outfile}")

def main(args):
    # find image files
    img_files = find_image_files(args.input_dir)
    # filter images by file type
    img_files = filter_img_files(img_files, args.file_type)
    # group files
    img_groups = group_img_files(img_files)
    # filter images by test image names or count
    img_groups = select_img_groups(
        img_groups, args.test_image_names, args.test_image_count
    )
    # create symlinks
    img_groups = create_symlinks(img_groups, args.output_dir)
    # write group table
    write_group_table(img_groups)

## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)