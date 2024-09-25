#!/usr/bin/env python
# import
## batteries
import os
import time
import logging
import argparse
import requests
from typing import Tuple
## 3rd party
import numpy as np
import numpy.random as random
import tifffile
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from IPython.display import HTML

# logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Simulate calcium imaging data"
epi = """DESCRIPTION:
 Generates a simulated movie of puffs based on a model puff loaded from an image file
and writes TIFF metadata including exposure time.
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument('STK_file', type=str, help='Path to the STK file')
parser.add_argument('--num_frames', type=int, default=1000, 
                    help='Number of frames in the movie')
parser.add_argument('--puff_intensity', type=int, default=5, 
                    help='Amplitude of the puffs')
parser.add_argument('--num_puffs', type=int, default=10, 
                    help='Number of puffs to simulate')
parser.add_argument('--img_width', type=int, default=128, 
                    help='Width of the movie frame')
parser.add_argument('--img_ht', type=int, default=128, 
                    help='Height of the movie frame')
parser.add_argument('--noise_free', action='store_true', 
                    help='Generate a noise-free movie')
parser.add_argument('--output_dir', type=str, default='.', 
                    help='Directory where the files will be saved')
parser.add_argument('--base_fname', type=str, default='synthetic_puffs', 
                    help='Base file name for saving files')
parser.add_argument('--retries', type=int, default=5, 
                    help='Number of retries for loading the STK file')
parser.add_argument('--delay', type=int, default=1, 
                    help='Time in seconds to wait between retries if loading fails')
parser.add_argument('--exposure_time', type=int, default=8, 
                    help='Exposure time in seconds for the simulation')

# functions
def main(args) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a simulated movie of puffs based on a model puff loaded from an image file
    and writes TIFF metadata including exposure time.

    Parameters:
    - See argparse help for details

    Returns:
    - simulated_movie: 3D array representing the simulated movie with puffs
    - puff_positions: Array of puff positions and times
    """
    # Load the puff model from the STK file
    with tifffile.TiffFile(args.STK_file) as tif:
        puff = tif.asarray() 
            
    # Reshape and process the loaded puff file
    puff = puff.reshape(puff.shape[0:3])
    puff = puff.astype(np.float64)

    # Normalize the puff model: Subtract baseline and scale to a max value of 1
    puff -= puff[0:10].mean(0)
    puff /= puff.max()

    # Initialize the movie array where the puffs will be added
    if args.noise_free:
        sim_mov = np.zeros((args.num_frames, args.img_width, args.img_ht), dtype=float)  # No noise
    else:
        sim_mov = random.randn(args.num_frames, args.img_width, args.img_ht)  # Add random Gaussian noise

    (t_step, puff_ht, puff_wd) = puff.shape
    puff_pos = []
    
    # Offset to control where peak puff appears
    puff_offset = np.array([18, 9.578511, 9.33569])
    
    # Add puffs to the movie, use tqdm to show progress bar
    logging.info(f'Adding puffs to the movie...')
    for i in np.arange(args.num_puffs):
        # Randomly select the start time and position for the puff
        start_t = random.randint(0, args.num_frames - t_step)
        if args.img_width - puff_wd < 1:
            x_pos = 0
        else:
            x_pos = random.randint(0, args.img_width - puff_wd)
        if args.img_ht - puff_ht < 1:
            y_pos = 0
        else:
            y_pos = random.randint(0, args.img_ht - puff_ht)

        # Define the time and spatial indices where the puff will be added
        time_indices = np.arange(start_t, start_t + t_step, dtype=int)
        x_indices = np.arange(x_pos, x_pos + puff_wd, dtype=int)
        y_indices = np.arange(y_pos, y_pos + puff_ht, dtype=int)

        # Add the puff to the movie array at the selected time and position
        sim_mov[np.ix_(time_indices, x_indices, y_indices)] += args.puff_intensity * puff

        # Store puff information
        puff_pos.append([start_t + puff_offset[0], x_pos + puff_offset[1], y_pos + puff_offset[2]])
    
    # Convert the list of puff positions to a numpy array and sort by time
    puff_pos = np.array(puff_pos)
    puff_pos = puff_pos[puff_pos[:, 0].argsort()]  # Sort by time

    # Save the movie and puff positions if required
    ## Expand the user directory and create output directory if it doesn't exist
    output_dir = os.path.expanduser(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    ## Save the puff positions to a CSV file
    puff_positions_file = os.path.join(output_dir, f'{args.base_fname}_puff_positions.csv')
    np.savetxt(puff_positions_file, puff_pos, delimiter=',', header='Time,X,Y', comments='')
    logging.info(f'Puff positions saved to {puff_positions_file}')

    ## Metadata to be written into TIFF file
    desc = f'Acquired from Synthetic Pipeline\nExposure: {args.exposure_time} msec\nBinning: 1x1'
    desc += '\nRegion: 128 x 128, offset at (0,0)\nSensor Mode: Normal\n'
    metadata = {
        'ImageDescription': desc,
        'Software': 'SyntheticPuffGenerator',
        'BitsPerSample': 16,
        'SamplesPerPixel': 1
    }

    ## Save the movie as a multi-page TIFF
    movie_file = os.path.join(output_dir, f'{args.base_fname}_movie.tiff')
    tifffile.imwrite(movie_file, sim_mov.astype(np.uint8), metadata=metadata)
    logging.info(f'Movie saved as TIFF to {movie_file}')

## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)