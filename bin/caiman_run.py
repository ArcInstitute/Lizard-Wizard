#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import logging
import argparse
## 3rd party
import caiman as cm
## source


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

# functions
def main(args):
     # Create a memory-mapped file using CaImAn from the temp file
    fname_new = cm.save_memmap(img_file, base_name='memmap_', order='C')

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)