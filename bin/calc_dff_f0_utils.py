# import
## batteries
import os
import logging
## 3rd party
import numpy as np
import tifffile
import matplotlib.pyplot as plt
from scipy import ndimage as ndi


# functions
def check_and_load_file(file_path: str):
    """
    Checks if a file exists and loads it based on its extension.
    Args:
        file_path: Path to the file to be loaded.
    Returns:
        Loaded file content if successful, otherwise None.
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        logging.warning(f'File {file_path} does not exist.')
        return None

    # Load the file based on its extension
    print(f'Opening {os.path.basename(file_path)}')
    try:
        # Determine the file type by extension and load accordingly
        if file_path.endswith('.npy'):
            return np.load(file_path)
        elif file_path.endswith('.tif') or file_path.endswith('.tiff'):
            return tifffile.imread(file_path)
        else:
            error_msg = f'Unsupported file type for file {os.path.basename(file_path)}'
            logging.warning(error_msg)
    except Exception as e:
        error_msg = f'Error opening file {os.path.basename(file_path)}: {e}'
        logging.warning(error_msg)
    return None
   

def convert_f_to_dff_perc(f_mat, perc, win_sz=500):
    """
    Converts fluorescence data to delta F/F using a percentile filter.
    
    Parameters:
    f_mat (ndarray): Fluorescence data matrix with neurons as rows and time points as columns.
    perc (int): Percentile value for the filter.
    win_sz (int): Window size for the percentile filter.
    
    Returns:
    dff_mat (ndarray): Delta F/F matrix.
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

def plot_stacked_traces(dff_dat, time_points, title="Stacked ΔF/F₀ Traces"):
    """
    Plots stacked traces of ΔF/F₀ for multiple neurons over time.
    
    Parameters:
    dff_dat (ndarray): Delta F/F₀ data matrix with neurons as rows and time points as columns.
    time_points (ndarray): Array of time points corresponding to the columns in dff_dat.
    title (str): Title of the plot. Default is "Stacked ΔF/F₀ Traces".
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


def draw_dff_activity(act_dat, act_filt_nsp_ids, max_dff_int, begin_tp, end_tp, sz_per_neuron, analysis_dir, base_fname, n_start=0, n_stop=-1, dff_bar=1, frate=30, lw=.2):
    """
    Plots the activity data of neurons within a specified time range.
    
    Parameters:
    act_dat (ndarray): Activity data matrix with neurons as rows and time points as columns.
    act_filt_nsp_ids (array): Array of neuron IDs corresponding to the rows of act_dat.
    max_dff_int (float): Maximum ΔF/F intensity for scaling the plot.
    begin_tp (int): Starting time point for the plot.
    end_tp (int): Ending time point for the plot.
    n_start (int): Index of the first cell to plot.
    n_stop (int): Index of the last cell to plot.
    dff_bar (float): Height of the ΔF/F scale bar.
    frate (int): Frames per second of the data.
    lw (float): Line width of the plot.
    analysis_dir (str): Directory where the plot will be saved.
    base_fname (str): Base filename for the plot.
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


def overlay_images(im_avg, binary_overlay, overlay_color=[255, 255, 0]):
    """
    Create an overlay image with a specific color for the binary overlay and gray for the background.

    Parameters:
    im_avg (ndarray): The average image (grayscale).
    binary_overlay (ndarray): The binary overlay image.
    overlay_color (list): The RGB color for the binary overlay.

    Returns:
    overlay_image (ndarray): The combined overlay image.
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

def create_montage(images, im_avg, grid_shape, overlay_color=[255, 255, 0], rescale_intensity=False):
    """
    Creates a montage from a list of images arranged in a specified grid shape,
    with an overlay color applied to binary images and gray background.

    Parameters:
    images (list of ndarray): List of binary images to be arranged in a montage.
    im_avg (ndarray): The average image (grayscale) for background.
    grid_shape (tuple): Shape of the grid for arranging the images (rows, columns).
    overlay_color (list): The RGB color for the binary overlay.
    rescale_intensity (bool): Flag to indicate if image intensity should be rescaled. Default is False.

    Returns:
    montage (ndarray): Montage image.
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