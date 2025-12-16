# import
## batteries
import os
import logging
from typing import List, Tuple
## 3rd party
import numpy as np
import tifffile
import matplotlib.pyplot as plt
from scipy import ndimage as ndi


# functions
def save_dff_dat(f_dat, dff_dat, base_fname, output_dir):
    logging.info(f'Saving f-dat and dff-dat for {base_fname}')

    # save f and dff data
    np.save(os.path.join(output_dir, f'{base_fname}_f-dat.npy'), f_dat)
    np.save(os.path.join(output_dir, f'{base_fname}_dff-dat.npy'), dff_dat)

def define_slice_extraction(file_type: str, A: np.ndarray, im: np.ndarray,
                            im_shape: np.ndarray, im_bg: np.ndarray) -> tuple:
    """
    Define the slice extraction logic based on file type.
    Args:
        file_type: Type of the file being processed.
        A: Spatial components matrix.
        im: Image data.
        im_shape: Shape of the image data.
        im_bg: Background image data.
    Returns:
        f_dat: Fluorescence data matrix.
        slice_indices: Indices for slicing the image data.
        slice_extraction: Function for extracting slices from the image data.
    """
    logging.info(f'Defining slice extraction for {file_type}')

    # Define slice extraction logic based on file type
    if file_type.lower() == 'moldev':
        # Initialize storage for fluorescence data if moldev
        f_dat = np.zeros((A.shape[1], im_shape[0]), dtype='float')
        slice_indices = range(im.shape[0])
        slice_extraction = lambda im, z: im[z, :, :]
    elif file_type.lower() == 'zeiss':
        # Initialize storage for fluorescence data
        f_dat = np.zeros((A.shape[1], im.shape[1]), dtype='float')
        slice_indices = range(im.shape[1])
        slice_extraction = lambda im, z: im[0, z, 0, :, :]

    return f_dat, slice_indices, slice_extraction

def calc_mean_signal(im: np.ndarray, slice_indices: List[int], 
                     slice_extraction: callable,  A: np.ndarray, dict_mask: dict,
                     im_bg: np.ndarray, f_dat: np.ndarray, fname: str
                     ) -> np.ndarray:
    """
    Calculate the mean fluorescence signal for each component in the image.
    Args:
        im: Image data.
        slice_indices: Indices for slicing the image data.
        slice_extraction: Function for extracting slices from the image data.
        A: Spatial components matrix.
        dict_mask: Dictionary containing masks for each component.
        im_bg: Background image data.
        f_dat: Fluorescence data matrix.
        fname: Filename of the image being processed.
    Returns:
        f_dat: Fluorescence data matrix.
    """
    # Process each z-slice of the image to compute mean fluorescence
    for z in slice_indices:
        z_slice = slice_extraction(im, z)
        for j in range(A.shape[1]):
            try:
                if dict_mask[j].shape == z_slice.shape:
                    f_dat[j, z] = np.mean(z_slice[dict_mask[j]])
                else:
                    error_msg = f'Shape mismatch: z_slice shape {z_slice.shape} and mask shape {dict_mask[j].shape} do not match'
                    logging.warning(error_msg)
            except Exception as e:
                error_msg = f"Error in calc_dff_f0 for file {fname}: {e}"
                logging.warning(error_msg)
    
    # Subtract background and adjust negative values
    f_dat -= im_bg
    f_dat[f_dat < 0] = 0
    f_dat += 2

    return f_dat

def check_and_load_file(file_path: str) -> np.ndarray:
    """
    Checks if a file exists and loads it based on its extension.
    If "no-mask" file, return None.
    Args:
        file_path: Path to the file to be loaded.
    Returns:
        Loaded file content if successful, otherwise None.
    """
    # if masked named "_no-mask.tif", then return None
    if file_path.endswith('no-masks.tif'):
        logging.info("Mask file is 'no-masks', so not using")
        return None

    # Load the file based on its extension
    logging.info(f"Opening {os.path.basename(file_path)}")
    try:
        # Determine the file type by extension and load accordingly
        if file_path.endswith('.npy'):
            return np.load(file_path)
        elif file_path.endswith('.tif') or file_path.endswith('.tiff'):
            return tifffile.imread(file_path)
        else:
            error_msg = f"Unsupported file type for file {os.path.basename(file_path)}"
            logging.warning(error_msg)
    except Exception as e:
        error_msg = f"Error opening file {os.path.basename(file_path)}: {e}"
        logging.warning(error_msg)
    return None
   
def convert_f_to_dff_perc(f_mat: np.ndarray, perc: int, win_sz: int=500) -> np.ndarray:
    """
    Convert fluorescence data to delta F/F using a percentile filter.
    Args:
        f_mat: Fluorescence data matrix with neurons as rows and time points as columns.
        perc: Percentile value for the filter.
        win_sz: Window size for the percentile filter.
    Returns:
        dff_mat: Delta F/F matrix.
    """
    logging.info(f'Generating dff with perc {perc} and win_sz {win_sz}')

    # Allocate array for baseline
    f_base = np.zeros_like(f_mat)
    
    # Apply the percentile filter row-wise
    for j in range(f_base.shape[0]):
        f_base[j, :] = ndi.percentile_filter(f_mat[j, :], perc, size=win_sz)
    
    # Calculate ΔF/F
    dff_mat = (f_mat - f_base) / f_base
    dff_mat[dff_mat < 0] = 0
    
    return dff_mat

def plot_stacked_traces(dff_dat: np.ndarray, time_points: np.ndarray, 
                        title: str="Stacked ΔF/F₀ Traces") -> None:
    """
    Plot stacked traces of ΔF/F₀ for multiple neurons over time.
    Args:
        dff_dat: Delta F/F₀ data matrix with neurons as rows and time points as columns.
        time_points: Array of time points corresponding to the columns in dff_dat.
        title: Title of the plot. Default is "Stacked ΔF/F₀ Traces".
    """
    # Ensure dff_dat and time_points are numpy arrays
    dff_dat = np.array(dff_dat)
    time_points = np.array(time_points)
    
    # Number of neurons/components
    num_neurons = dff_dat.shape[0]
    
    # Offset for stacking traces
    offset = 2 * np.max(np.abs(dff_dat))
    
    # Create a figure
    plt.figure(figsize=(12, 8))
    
    # Plot each trace with an offset
    for neuron_idx in range(num_neurons):
        plt.plot(time_points, dff_dat[neuron_idx, :] + neuron_idx * offset, label=f'Neuron {neuron_idx+1}')
    
    # Labeling the plot
    plt.xlabel('Time (frames)')
    plt.ylabel('ΔF/F₀')
    plt.title(title)
    plt.yticks([])
    # plt.show()

def draw_dff_activity(act_dat: np.ndarray, act_filt_nsp_ids: np.array, max_dff_int: float, 
                      begin_tp: int, end_tp: int, sz_per_neuron, output_dir: str, 
                      base_fname: str, n_start: int=0, n_stop: int=-1, dff_bar: float=1.0, 
                      frate: int=30, lw: float=0.2) -> None:
    """
    Plot the activity data of neurons within a specified time range.
    Args:
        act_dat: Activity data matrix with neurons as rows and time points as columns.
        act_filt_nsp_ids: Array of neuron IDs corresponding to the rows of act_dat.
        max_dff_int: Maximum ΔF/F intensity for scaling the plot.
        begin_tp: Starting time point for the plot.
        end_tp: Ending time point for the plot.
        output_dir: Directory where the plot will be saved.
        base_fname: Base filename for the plot.
        n_start: Index of the first cell to plot.
        n_stop: Index of the last cell to plot.
        dff_bar: Height of the ΔF/F scale bar.
        frate: Frames per second of the data.
        lw: Line width of the plot.
    """
    logging.info(f'Plotting ΔF/F₀ activity for {base_fname}')
    logging.disable(logging.WARNING)

    # Ensure valid end_tp
    end_tp = end_tp if end_tp >= 0 else act_dat.shape[1]
    
    # Sort the data by neuron IDs and select the time range
    sorted_indices = np.argsort(act_filt_nsp_ids)
    act_dat_sorted = act_dat[sorted_indices, begin_tp:end_tp]
    act_filt_nsp_ids_sorted = act_filt_nsp_ids[sorted_indices]
    
    # Determine the number of neurons to plot
    if n_stop is None or n_stop < 0:
        n_stop = act_dat_sorted.shape[0]
    n_neurons = min(n_stop, act_dat_sorted.shape[0])
    
    # Scale the maximum ΔF/F value
    max_dff_int = max(max_dff_int / 2, 0.25)
    
    # Create a time vector
    time_vector = np.arange(act_dat_sorted.shape[1]) / frate

    # Calculate plot height
    gr_ht = np.maximum(1, int(act_dat_sorted.shape[0] * sz_per_neuron))

    # Create a figure for the plot
    fig, ax = plt.subplots(1, 1, figsize=(7 / 2, gr_ht / 2), sharey=True)

    # Plot the activity data for each neuron
    for i in range(n_start, n_neurons):
        color_str = f'C{i % 9}'  # Cycle through 9 colors
        ax.plot(time_vector, act_dat_sorted[i, :] + (n_neurons - i - 1) * max_dff_int, linewidth=lw, color=color_str)
    
    # Draw a vertical line indicating the ΔF/F scale in black
    ax.vlines(x=-1., ymin=0, ymax=dff_bar, lw=2, color='black')
    ax.text(-1.5, dff_bar / 2, f'{dff_bar} ΔF/F', ha='center', va='center', rotation='vertical')
    
    # Label the x-axis
    ax.set_xlabel('Time(s)')

    # Hide the top, right, and left spines (borders)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Hide the y-axis ticks and labels
    ax.yaxis.set_ticks([])
    ax.yaxis.set_ticklabels([])

    # Adjust the margins of the plot
    ax.margins(0.008)
    
    # Display the plot
    # plt.show()

    # Save plot
    fig.savefig(os.path.join(output_dir, f'{base_fname}_df-f0-graph.png'), format='png')
    logging.disable(logging.NOTSET)

def overlay_images(im_avg: np.ndarray, binary_overlay: np.ndarray, 
                   overlay_color: list=[255, 255, 0]) -> np.ndarray:
    """
    Create an overlay image with a specific color for the binary overlay and gray for the background.
    Args:
        im_avg: The average image (grayscale).
        binary_overlay: The binary overlay image.
        overlay_color: The RGB color for the binary overlay.
    Returns:
        overlay_image: The combined overlay image.
    """
    # Normalize the grayscale image to the range [0, 255]
    im_avg_norm = (255 * (im_avg - np.min(im_avg)) / (np.max(im_avg) - np.min(im_avg))).astype(np.uint8)
    
    # Convert grayscale image to 3-channel RGB
    im_avg_rgb = np.stack([im_avg_norm] * 3, axis=-1)
    
    # Create an RGB overlay with the specified color
    overlay_rgb = np.zeros_like(im_avg_rgb)
    overlay_rgb[binary_overlay > 0] = overlay_color
    
    # Combine the two images
    combined_image = np.where(binary_overlay[..., None] > 0, overlay_rgb, im_avg_rgb)
    
    return combined_image

def create_montage(images: List[np.ndarray], im_avg: np.ndarray, grid_shape: Tuple[int, int], 
                   overlay_color: list=[255, 255, 0], rescale_intensity: bool=False) -> np.ndarray:
    """
    Create a montage from a list of images arranged in a specified grid shape,
    with an overlay color applied to binary images and gray background.
    Args:
        images: List of binary images to be arranged in a montage.
        im_avg: The average image (grayscale) for background.
        grid_shape: Shape of the grid for arranging the images (rows, columns).
        overlay_color: The RGB color for the binary overlay.
        rescale_intensity: Flag to indicate if image intensity should be rescaled. Default is False.
    Returns:
        montage: Montage image.
    """
    # Calculate the shape of the montage grid
    n_images = len(images)
    img_height, img_width = im_avg.shape[:2]
    montage_height = grid_shape[0] * img_height
    montage_width = grid_shape[1] * img_width

    # Create an empty array for the montage
    montage = np.zeros((montage_height, montage_width, 3), dtype=np.uint8)

    # Populate the montage array with overlay images
    for idx, img in enumerate(images):
        y = idx // grid_shape[1]
        x = idx % grid_shape[1]
        overlay_img = overlay_images(im_avg, img, overlay_color)
        montage[y * img_height:(y + 1) * img_height, x * img_width:(x + 1) * img_width] = overlay_img

    return montage

def plot_montage(montage_image: np.ndarray, outfile: str) -> None:
    """
    Plot the montage image and save it to a file.
    Args:
        montage_image: The montage image to be plotted.
        outfile: Path to save the montage image.
    """
    # Set logging level to WARNING to suppress matplotlib debug messages
    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    # Plot the montage for all components
    plt.figure(figsize=(10, 10))
    plt.imshow(montage_image)
    plt.title('Montage of All df/f0 spatial components')
    plt.axis('off')

    # Save the montage image
    #plt.show()
    plt.savefig(outfile)
    plt.close()
    logging.info(f"Montage image saved to {outfile}")

    # Reset logging level to INFO
    logging.getLogger('matplotlib').setLevel(logging.INFO)