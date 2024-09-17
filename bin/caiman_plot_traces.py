import logging
import numpy as np
import matplotlib.pyplot as plt


def plot_traces(all_traces, accepted_components, original_data=None, frate=1.0, zoom_factor=1.0, 
                trace_height_factor=0.2, base_height=4, trace_type='denoised', outfile: str='trace_plot.png'):
    """
    Plots the accepted and rejected calcium traces (either original or denoised) vertically stacked with the same y-scale.

    Parameters:
    - all_traces (object): The object containing all the traces, typically an instance of a class with the attribute 'C' which holds the trace data.
    - accepted_components (list): List of indices for the accepted components.
    - original_data (np.ndarray, optional): The original trace data. Required if `trace_type` is 'original'.
    - frate (float): Frame rate.
    - zoom_factor (float): Factor to zoom the traces vertically.
    - trace_height_factor (float): Height increment per trace.
    - base_height (float): Base height for a subplot with few traces.
    - trace_type (str): Either 'original' or 'denoised' to specify which traces to plot.
    - outfile (str): The output file name.

    The function will display two vertically stacked plots: one for the accepted traces and one for the rejected traces.
    """
    
    # Select the traces to plot based on trace_type
    if trace_type == 'original' and original_data is not None:
        data_to_plot = original_data
    else:
        data_to_plot = all_traces.C

    # Extract accepted and rejected traces
    accepted_traces = data_to_plot[accepted_components, :]
    rejected_components = [i for i in range(data_to_plot.shape[0]) if i not in accepted_components]
    rejected_traces = data_to_plot[rejected_components, :]

    time_vector = np.arange(data_to_plot.shape[1]) / float(frate)

    # Determine the y-limits based on both accepted and rejected traces
    y_min, y_max = np.min(data_to_plot), np.max(data_to_plot)

    # Number of neurons and time points
    num_accepted_neurons = accepted_traces.shape[0]
    num_rejected_neurons = rejected_traces.shape[0]

    # Calculate the figure height dynamically based on the number of traces
    accepted_height = base_height + trace_height_factor * num_accepted_neurons
    rejected_height = base_height + trace_height_factor * num_rejected_neurons
    total_height = accepted_height + rejected_height

    # Create vertically stacked subplots
    fig, axes = plt.subplots(2, 1, figsize=(7 / 2, total_height), gridspec_kw={'height_ratios': [accepted_height, rejected_height]}, sharex=True)

    # Offset for stacking the traces vertically
    offset_increment = (y_max - y_min) * 1.1 * zoom_factor

    def plot_trace_group(traces, ax, title, offset_increment):
        offset = 0
        for i in range(traces.shape[0]):
            ax.plot(time_vector, traces[i] + offset, lw=1)
            offset += offset_increment
        ax.set_title(title)
        ax.set_xlabel('Time (seconds)')
        ax.yaxis.set_ticks([])
        ax.set_ylim([y_min, y_min + offset])

        # Add a y-axis scale bar
        scale_bar_length = y_max - y_min
        scale_bar_y_start = y_min
        scale_bar_x_position = -0.05 * (time_vector[-1] - time_vector[0])
        ax.plot([scale_bar_x_position, scale_bar_x_position],
                [scale_bar_y_start, scale_bar_y_start + scale_bar_length], color='black', lw=2)
        ax.text(scale_bar_x_position, scale_bar_y_start + scale_bar_length / 2,
                f'{scale_bar_length:.2f} a.u.', rotation=90,
                verticalalignment='center', horizontalalignment='right',
                color='black', fontsize=10)

        # Hide spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

    # Plot accepted and rejected traces
    plot_trace_group(accepted_traces, axes[0], f'Accepted {trace_type.capitalize()} Calcium Traces', offset_increment)
    plot_trace_group(rejected_traces, axes[1], f'Rejected {trace_type.capitalize()} Calcium Traces', offset_increment)

    # Format the layout
    plt.tight_layout()

    # Save the figure
    plt.savefig(outfile, format=outfile.split('.')[-1], bbox_inches='tight')
    logging.info(f"Saved original trace plot to {outfile}")


def plot_original_traces(all_traces: object, accepted_components: list, 
                         original_data: np.ndarray, frate: float, 
                         outfile: str, zoom_factor: float=1.0) -> None:
    """
    Plots the accepted and rejected original calcium traces vertically stacked with the same y-scale.
    The function will display two vertically stacked plots: one for the accepted traces and one for the rejected traces.

    Args:
        all_traces: The object containing all the traces, typically an instance of a class with the attribute 'C' which holds the trace data.
        accepted_components: List of indices for the accepted components.
        original_data: The original trace data.
        frate: The frame rate of the recording.
        outfile: The output file name.
        zoom_factor: The zoom factor for the y-axis.
    """
    # Extract accepted and rejected original traces
    accepted_traces = original_data[accepted_components, :]
    rejected_components = [i for i in range(original_data.shape[0]) if i not in accepted_components]
    rejected_traces = original_data[rejected_components, :]

    # Determine the y-limits based on both accepted and rejected traces
    y_min, y_max = np.min(original_data), np.max(original_data)

    # Number of neurons and time points
    num_accepted_neurons = accepted_traces.shape[0]
    num_rejected_neurons = rejected_traces.shape[0]
    num_timepoints = original_data.shape[1]
    ## Create a time vector
    time_vector = np.arange(all_traces.C.shape[1]) / float(frate)

    # Calculate the figure height dynamically based on the number of traces
    base_height = 4  # Base height for a subplot with few traces
    trace_height_factor = 0.2  # Height increment per trace

    accepted_height = base_height + trace_height_factor * num_accepted_neurons
    rejected_height = base_height + trace_height_factor * num_rejected_neurons
    total_height = accepted_height + rejected_height

    # Create vertically stacked subplots
    fig, axes = plt.subplots(2, 1, figsize=((7/2), total_height), gridspec_kw={'height_ratios': [accepted_height, rejected_height]}, sharex=True)

    # Offset for stacking the traces vertically
    offset_increment = (y_max - y_min) * 1.1 * zoom_factor

    def plot_traces(traces, ax, title, offset_increment) -> None:
        offset = 0
        for i in range(traces.shape[0]):
            ax.plot(time_vector, traces[i] + offset, lw=1)  # lw is line width
            offset += offset_increment
        ax.set_title(title)
        ax.set_xlabel('Time (seconds)')
        ax.yaxis.set_ticks([])
        ax.set_ylim([y_min, y_min + offset])

        # Introduce a scale bar for the y-axis
        scale_bar_length = y_max - y_min  # Set the scale bar length to the range of the y-axis
        scale_bar_y_start = y_min  # Start the scale bar at the bottom of the plot
        scale_bar_x_position = -0.05 * (time_vector[-1] - time_vector[0])  # 5% of the time axis length to the left of the plot
        ax.plot([scale_bar_x_position, scale_bar_x_position],
                [scale_bar_y_start, scale_bar_y_start + scale_bar_length], color='black', lw=2)
        ax.text(scale_bar_x_position, scale_bar_y_start + scale_bar_length / 2,
                f'{scale_bar_length:.2f} a.u.', rotation=90,
                verticalalignment='center', horizontalalignment='right',
                color='black', fontsize=10)
        
        # Hide the top, right, and left spines (borders)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

    # Plot accepted traces
    plot_traces(accepted_traces, axes[0], 'Accepted Original Calcium Traces', offset_increment)

    # Plot rejected traces
    plot_traces(rejected_traces, axes[1], 'Rejected Original Calcium Traces', offset_increment)

    # Adjust the layout
    plt.tight_layout()

    # save the figure
    plt.savefig(outfile, format=outfile.split('.')[-1], bbox_inches='tight')
    logging.info(f"Saved original trace plot to {outfile}")


def plot_denoised_traces(all_traces: object, accepted_components: list, frate: float, 
                         outfile: str, zoom_factor: float=1.0) -> None:
    """
    Plots the accepted and rejected denoised calcium traces vertically stacked with the same y-scale.
    The function will display two vertically stacked plots: one for the accepted traces and one for the rejected traces.

    Args:
        all_traces: The object containing all the traces, typically an instance of a class with 'C' which holds the denoised trace data.
        accepted_components: List of indices for the accepted components.
        frate: The frame rate of the recording.
        outfile: The output file name.
        zoom_factor: The zoom factor for the y-axis.
    """
    # Extract accepted and rejected traces
    accepted_traces = all_traces.C[accepted_components, :]
    rejected_components = [i for i in range(all_traces.C.shape[0]) if i not in accepted_components]
    rejected_traces = all_traces.C[rejected_components, :]

    time_vector = np.arange(all_traces.C.shape[1]) / float(frate)

    # Determine the y-limits based on both accepted and rejected traces
    y_min, y_max = np.min(all_traces.C), np.max(all_traces.C)

    # Number of neurons and time points
    num_accepted_neurons = accepted_traces.shape[0]
    num_rejected_neurons = rejected_traces.shape[0]
    num_timepoints = all_traces.C.shape[1]

    # Calculate the figure height dynamically based on the number of traces
    base_height = 4  # Base height for a subplot with few traces
    trace_height_factor = 0.2  # Height increment per trace

    accepted_height = base_height + trace_height_factor * num_accepted_neurons
    rejected_height = base_height + trace_height_factor * num_rejected_neurons
    total_height = accepted_height + rejected_height

    # Create vertically stacked subplots
    fig, axes = plt.subplots(2, 1, figsize=(7/2, total_height), gridspec_kw={'height_ratios': [accepted_height, rejected_height]}, sharex=True)

    # Offset for stacking the traces vertically
    offset_increment = (y_max - y_min) * 1.1 * zoom_factor

    def plot_traces(traces, ax, title, offset_increment) -> None:
        offset = 0
        for i in range(traces.shape[0]):
            ax.plot(time_vector, traces[i] + offset, lw=1)  # lw is line width
            offset += offset_increment
        ax.set_title(title)
        ax.set_xlabel('Time (seconds)')
        ax.yaxis.set_ticks([])
        ax.set_ylim([y_min, y_min + offset])

        # Introduce a scale bar for the y-axis
        scale_bar_length = y_max - y_min  # Set the scale bar length to the range of the y-axis
        scale_bar_y_start = y_min  # Start the scale bar at the bottom of the plot
        scale_bar_x_position = -0.05 * (time_vector[-1] - time_vector[0])  # 5% of the time axis length to the left of the plot
        ax.plot([scale_bar_x_position, scale_bar_x_position],
                [scale_bar_y_start, scale_bar_y_start + scale_bar_length], color='black', lw=2)
        ax.text(scale_bar_x_position, scale_bar_y_start + scale_bar_length / 2,
                f'{scale_bar_length:.2f} a.u.', rotation=90,
                verticalalignment='center', horizontalalignment='right',
                color='black', fontsize=10)
        
        # Hide the top, right, and left spines (borders)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

    # Plot accepted traces
    plot_traces(accepted_traces, axes[0], 'Accepted Denoised Calcium Traces', offset_increment)

    # Plot rejected traces
    plot_traces(rejected_traces, axes[1], 'Rejected Denoised Calcium Traces', offset_increment)

    # Adjust the layout
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(outfile, format=outfile.split('.')[-1], bbox_inches='tight')
    logging.info(f"Saved denoised trace plot to {outfile}")

