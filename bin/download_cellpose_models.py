#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import os
import logging
import argparse
## 3rd party
import numpy as np
from cellpose import models

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Download cellpose models"
epi = """DESCRIPTION:
Download cellpose models for nuclei and cytoplasmic segmentation.
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument("output_dir", type=str,
                    help="Output directory to save models")

def main(args):
    os.makedirs(args.output_dir, exist_ok=True)
    nuclei_model = models.Cellpose(gpu=False, model_type='nuclei')
    cyto3_model = models.Cellpose(gpu=False, model_type='cyto3')
    logging.info(f"Models downloaded to: {args.output_dir}")

## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)