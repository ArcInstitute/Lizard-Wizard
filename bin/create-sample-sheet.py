#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import sys
import shutil
import logging
import argparse

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = 'Create a sample sheet from a directory of image files'
epi = """DESCRIPTION:
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('input_dir', type=str,
                    help='Directory path containing the image files')
parser.add_argument('--version', action='version', version='0.1.0')


def main(args):
    pass


## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)