#!/usr/bin/env python
# import
## batteries
import os
import time
import json
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
## package
from load_tiff import load_image_data_moldev_concat

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
#parser.add_argument('metadata_file', type=str, help='Path to the metadata file')
parser.add_argument('--num_simulations', type=int, default=1, 
                    help='Number of movies to simulate')
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
def get_metadata():
    return {'BitsPerSample': 16,
 'Compression': '<COMPRESSION.NONE: 1>',
 'ImageDescription': '{"NewSubfileType": 2, "ImageWidth": 512, "ImageLength": '
                     '512, "BitsPerSample": 16, "Compression": 1, '
                     '"PhotometricInterpretation": 1, "ImageDescription": '
                     '"<MetaData>\n<prop id=\"Description\" '
                     'type=\"string\" value=\"Simulated from Synthetic Pipeline '
                     'Camera&#13;&#10;Exposure: 10 msec&#13;&#10;Binning: 4 X '
                     '4&#13;&#10;Region: 2048 x 2048, offset at (0, '
                     '0)&#13;&#10;Sensor Mode: Normal&#13;&#10;Digitizer: '
                     'Speed 3 (16-bit)&#13;&#10;Bit Depth: '
                     '16-bit&#13;&#10;Frames to Average: '
                     '1&#13;&#10;\"/>\n<prop id=\"MetaDataVersion\" '
                     'type=\"float\" value=\"1\"/>\n<prop '
                     'id=\"ApplicationName\" type=\"string\" '
                     'value=\"MetaMorph\"/>\n<prop '
                     'id=\"ApplicationVersion\" type=\"string\" '
                     'value=\"6.7.2.290\"/>\n<PlaneInfo>\n<prop '
                     'id=\"plane-type\" type=\"string\" '
                     'value=\"plane\"/>\n<prop id=\"pixel-size-x\" '
                     'type=\"int\" value=\"512\"/>\n<prop '
                     'id=\"pixel-size-y\" type=\"int\" '
                     'value=\"512\"/>\n<prop id=\"bits-per-pixel\" '
                     'type=\"int\" value=\"16\"/>\n<prop '
                     'id=\"autoscale-state\" type=\"bool\" '
                     'value=\"on\"/>\n<prop id=\"autoscale-min-percent\" '
                     'type=\"float\" value=\"0\"/>\n<prop '
                     'id=\"autoscale-max-percent\" type=\"float\" '
                     'value=\"0\"/>\n<prop id=\"scale-min\" '
                     'type=\"int\" value=\"0\"/>\n<prop '
                     'id=\"scale-max\" type=\"int\" '
                     'value=\"65535\"/>\n<prop '
                     'id=\"spatial-calibration-state\" type=\"bool\" '
                     'value=\"on\"/>\n<prop id=\"spatial-calibration-x\" '
                     'type=\"float\" value=\"2.7204\"/>\n<prop '
                     'id=\"spatial-calibration-y\" type=\"float\" '
                     'value=\"2.7204\"/>\n<prop '
                     'id=\"spatial-calibration-units\" type=\"string\" '
                     'value=\"um\"/>\n<prop id=\"image-name\" '
                     'type=\"string\" value=\"Stream\"/>\n<prop '
                     'id=\"threshold-state\" type=\"string\" '
                     'value=\"ThresholdOff\"/>\n<prop '
                     'id=\"threshold-low\" type=\"int\" '
                     'value=\"0\"/>\n<prop id=\"threshold-high\" '
                     'type=\"int\" value=\"65535\"/>\n<prop '
                     'id=\"threshold-color\" type=\"colorref\" '
                     'value=\"4080ff\"/>\n<prop id=\"zoom-percent\" '
                     'type=\"int\" value=\"160\"/>\n<prop id=\"gamma\" '
                     'type=\"float\" value=\"1\"/>\n<prop '
                     'id=\"look-up-table-type\" type=\"string\" '
                     'value=\"by-wavelength\"/>\n<prop '
                     'id=\"look-up-table-name\" type=\"string\" '
                     'value=\"Set By Wavelength\"/>\n<prop '
                     'id=\"photonegative-mode\" type=\"bool\" '
                     'value=\"off\"/>\n<prop '
                     'id=\"gray-calibration-curve-fit-algorithm\" '
                     'type=\"int\" value=\"4\"/>\n<prop '
                     'id=\"gray-calibration-values\" type=\"float-array\" '
                     'value=\"\"/>\n<prop id=\"gray-calibration-min\" '
                     'type=\"float\" value=\"-1\"/>\n<prop '
                     'id=\"gray-calibration-max\" type=\"float\" '
                     'value=\"-1\"/>\n<prop id=\"gray-calibration-units\" '
                     'type=\"string\" value=\"\"/>\n<prop '
                     'id=\"plane-guid\" type=\"guid\" '
                     'value=\"{FDF3A4FF-ACE5-4ACC-A771-EC908F3A4DCA}\"/>\n<prop '
                     'id=\"acquisition-time-local\" type=\"time\" '
                     'value=\"20240416 12:05:06.287\"/>\n<prop '
                     'id=\"modification-time-local\" type=\"time\" '
                     'value=\"20240416 12:05:57.107\"/>\n<prop '
                     'id=\"stage-position-x\" type=\"float\" '
                     'value=\"52629.9\"/>\n<prop id=\"stage-position-y\" '
                     'type=\"float\" value=\"22489.9\"/>\n<prop '
                     'id=\"z-position\" type=\"float\" '
                     'value=\"0\"/>\n<prop id=\"wavelength\" '
                     'type=\"float\" value=\"520\"/>\n<prop '
                     'id=\"camera-binning-x\" type=\"int\" '
                     'value=\"4\"/>\n<prop id=\"camera-binning-y\" '
                     'type=\"int\" value=\"4\"/>\n<prop '
                     'id=\"camera-chip-offset-x\" type=\"float\" '
                     'value=\"0\"/>\n<prop id=\"camera-chip-offset-y\" '
                     'type=\"float\" value=\"0\"/>\n<custom-prop id=\"89 '
                     'North 405 Intensity\" type=\"float\" '
                     'value=\"0\"/>\n<custom-prop id=\"Synthetic '
                     'Shutter\" type=\"string\" '
                     'value=\"Closed\"/>\n<custom-prop id=\"Synthetic '
                     'Intensity\" type=\"float\" '
                     'value=\"0\"/>\n<custom-prop id=\"Synthetic '
                     'Shutter\" type=\"string\" '
                     'value=\"Closed\"/>\n<custom-prop id=\"Synthetic '
                     'Intensity\" type=\"float\" '
                     'value=\"1\"/>\n<custom-prop id=\"Synthetic '
                     'Shutter\" type=\"string\" '
                     'value=\"Open\"/>\n<custom-prop id=\"Synthetic '
                     'Intensity\" type=\"float\" '
                     'value=\"0\"/>\n<custom-prop id=\"Synthetic '
                     'Shutter\" type=\"string\" '
                     'value=\"Closed\"/>\n<custom-prop id=\"Synthetic '
                     'Intensity\" type=\"float\" '
                     'value=\"0\"/>\n<custom-prop id=\"Synthetic '
                     'Shutter\" type=\"string\" '
                     'value=\"Closed\"/>\n<custom-prop id=\"Synthetic '
                     'Intensity\" type=\"float\" '
                     'value=\"0\"/>\n<custom-prop id=\"Synthetic '
                     'Shutter\" type=\"string\" '
                     'value=\"Closed\"/>\n<custom-prop id=\"Synthetic '
                     'Intensity\" type=\"float\" '
                     'value=\"0\"/>\n<custom-prop id=\"Synthetic '
                     'Shutter\" type=\"string\" '
                     'value=\"Closed\"/>\n<prop id=\"_IllumSetting_\" '
                     'type=\"string\" value=\"FITC\"/>\n<prop '
                     'id=\"_MagSetting_\" type=\"string\" value=\"10X '
                     'Plan Apo Lambda\"/>\n<custom-prop id=\"Synthetic '
                     'Micro Objective\" type=\"string\" value=\"10X Plan '
                     'Apo Lambda\"/>\n<custom-prop id=\"ImageXpress Micro '
                     'X\" type=\"float\" '
                     'value=\"52629.9\"/>\n<custom-prop id=\"Synthetic '
                     'Micro Y\" type=\"float\" '
                     'value=\"22489.9\"/>\n<custom-prop id=\"Synthetic '
                     'Micro Z\" type=\"float\" '
                     'value=\"9910.26\"/>\n<custom-prop id=\"Synthetic '
                     'Module Dichroic Wheel\" type=\"string\" value=\"FITC '
                     '(5035430)\"/>\n<custom-prop id=\"Synthetic Module '
                     'Disk\" type=\"string\" value=\"OUT - '
                     'Running\"/>\n<custom-prop id=\"Synthetic Module '
                     'Emission Wheel\" type=\"string\" value=\"FITC '
                     '(5076223)\"/>\n<custom-prop id=\"Lamp, Synthetic '
                     'Micro Transmitted Light\" type=\"float\" '
                     'value=\"0\"/>\n<custom-prop id=\"Shutter, '
                     'Synthetic Transmitted Light\" type=\"string\" '
                     'value=\"Closed\"/>\n</PlaneInfo>\n</MetaData>", '
                     '"Orientation": 1, "SamplesPerPixel": 1, "RowsPerStrip": '
                     '8, "StripByteCounts": [8192, 8192, 8192, 8192, 8192, '
                     '8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, '
                     '8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, '
                     '8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, '
                     '8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, '
                     '8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, '
                     '8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, 8192, '
                     '8192, 8192, 8192, 8192, 8192], "Software": "MetaSeries", '
                     '"DateTime": "20240416 12:05:06.287", "shape": [6000, '
                     '512, 512]}',
 'ImageLength': 512,
 'ImageWidth': 512,
 'PhotometricInterpretation': '<PHOTOMETRIC.MINISBLACK: 1>',
 'ResolutionUnit': '<RESUNIT.NONE: 1>',
 'RowsPerStrip': 512,
 'SamplesPerPixel': 1,
 'Software': 'tifffile.py',
 'StripByteCounts': (524288,),
 'StripOffsets': (6144,),
 'XResolution': (1, 1),
 'YResolution': (1, 1)}

def create_well_names(start=None, end=None):
    rows = "ABCDEFGHIJKLMNOP"
    cols = [f"{i:02d}" for i in range(1, 25)]
    well_names = [f"{row}{col}" for row in rows for col in cols]
    # Return the well names within the specified range
    if not start:
        start = 0
    if not end:
        end = len(well_names) + 1
    return well_names[start:end]

def create_movie(puff, sim_num: int, args: dict):
    """
    Create a movie with puffs and save it as a multi-page TIFF file
    Parameters:
    - puff: 3D numpy array representing the puff model
    - sim_num: Simulation number
    - args: Dictionary with the simulation parameters
    """
    # Initialize the movie array where the puffs will be added
    if args.noise_free:
        sim_mov = np.zeros(
            (args.num_frames, args.img_width, args.img_ht), dtype=float
        )  # No noise
    else:
        sim_mov = random.randn(
            args.num_frames, args.img_width, args.img_ht
        )  # Add random Gaussian noise

    # Unpack puff dimensions
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

    ## Output file basename
    well_name = create_well_names(sim_num, sim_num + 1)[0]
    base_fname = f'{args.base_fname}_sim-{sim_num}_{well_name}_s1_FITC_full'
    
    ## Save the puff positions to a CSV file
    puff_positions_file = os.path.join(output_dir, f'{base_fname}.csv')
    np.savetxt(puff_positions_file, puff_pos, delimiter=',', header='Time,X,Y', comments='')
    logging.info(f'Puff positions saved to {puff_positions_file}')

    ## Metadata to be written into TIFF file
    desc = f'Acquired from Synthetic Pipeline\nExposure: {args.exposure_time} msec\nBinning: 1x1'
    desc += '\nRegion: 128 x 128, offset at (0,0)\nSensor Mode: Normal\n'

    ## Save the movie as a multi-page TIFF
    movie_file = os.path.join(output_dir, f'{base_fname}.tif')
    tifffile.imwrite(movie_file, sim_mov.astype(np.uint8), metadata=get_metadata())
    logging.info(f'Movie saved as TIFF to {movie_file}')

    ## Check the metadata formatting
    load_image_data_moldev_concat(movie_file)

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
    # Load the metadata
    #with open(args.metadata_file, 'r') as inF:
    #    metadata = json.load(inF)
    #$metadata = get_metadata()
    #print(metadata); exit();

    # Load the puff model from the STK file
    with tifffile.TiffFile(args.STK_file) as tif:
        puff = tif.asarray() 
            
    # Reshape and process the loaded puff file
    puff = puff.reshape(puff.shape[0:3])
    puff = puff.astype(np.float64)

    # Normalize the puff model: Subtract baseline and scale to a max value of 1
    puff -= puff[0:10].mean(0)
    puff /= puff.max()

    # simulate movies
    for i in range(args.num_simulations):
        create_movie(puff, i, args)

## script main
if __name__ == '__main__':
    args = parser.parse_args()
    main(args)