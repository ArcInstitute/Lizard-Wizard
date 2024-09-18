#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import re
import sys
import logging
import argparse



# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Create metadata file"
epi = """DESCRIPTION:
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('img_basename', type=str, 
                    help='Sample name')
parser.add_argument('frate', type=str,
                    help='frate file')

# functions
def read_frate(infile: str) -> float:
    """
    Read in the frame rate from the specified file.
    Expected format: `FRATE=<frame rate>`
    Args:
        infile: The file containing the frame rate
    Returns:
        frate: The frame rate
    """
    # Read the frame rate from the file
    frate = None
    with open(infile, 'r') as f:
        line = f.readline().strip()
        if line.startswith("FRATE="):
            frate = float(line.split('=')[1])
    # Check if the frame rate was read successfully
    if frate is None:
        raise ValueError(f"Could not read frame rate from file {infile}")
    return frate

def get_well(img_basename: str) -> str:
    regex = re.compile(r"^.+_([A-Z][0-9]{2})_s[0-9]_FITC")
    match = regex.match(img_basename)
    if match is None:
        return ""
    return match.group(1)

def main(args):
    # load the frame rate
    frate = read_frate(args.frate)
    # extract the well
    well = get_well(args.img_basename)
    # write out the metadata table
    print(f"{args.img_basename},{well},{frate}")
    
    
## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)