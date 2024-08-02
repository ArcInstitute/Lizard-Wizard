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
    if file_path.endswith('_no-mask.tif'):
        logging.info("Mask file is 'no-mask', so not using")
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
    plt.show()


def draw_dff_activity(act_dat: np.ndarray, act_filt_nsp_ids: np.array, max_dff_int: float, 
                      begin_tp: int, end_tp: int, sz_per_neuron, analysis_dir: str, base_fname: str, 
                      n_start: int=0, n_stop: int=-1, dff_bar: float=1.0, frate: int=30, lw: float=0.2) -> None:
    """
    Plot the activity data of neurons within a specified time range.
    Args:
        act_dat: Activity data matrix with neurons as rows and time points as columns.
        act_filt_nsp_ids: Array of neuron IDs corresponding to the rows of act_dat.
        max_dff_int: Maximum ΔF/F intensity for scaling the plot.
        begin_tp: Starting time point for the plot.
        end_tp: Ending time point for the plot.
        analysis_dir: Directory where the plot will be saved.
        base_fname: Base filename for the plot.
        n_start: Index of the first cell to plot.
        n_stop: Index of the last cell to plot.
        dff_bar: Height of the ΔF/F scale bar.
        frate: Frames per second of the data.
        lw: Line width of the plot.
    """
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
    plt.show()

    # Save plot
    fig.savefig(os.path.join(analysis_dir, f'df_f0_graph_{base_fname}.tif'), format='tiff')


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