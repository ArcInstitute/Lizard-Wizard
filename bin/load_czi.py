import xml.etree.ElementTree as ET
import aicspylibczi
import xmltodict

def load_image_data_czi(fname: str) -> tuple:
    """
    Loads image data from a CZI file and extracts the frame rate.

    Args:
        fname: The file path of the CZI file to be loaded.

    Returns:
        A tuple containing the image data and the frame rate.
           - im: The image data read from the CZI file.
           - frate: The frame rate extracted from the metadata.
    """
    # Open the CZI file using the aicspylibczi library
    czi = aicspylibczi.CziFile(fname)
    
    # Read the image data from the CZI file
    im, _ = czi.read_image()
    
    # Convert the metadata to a string
    metadata_str = ET.tostring(czi.meta, encoding='unicode')
    
    # Parse the metadata string into a dictionary
    metadata_dict = xmltodict.parse(metadata_str)
    
    # Extract the frame rate from the metadata
    frate = get_frame_rate_targets(metadata_dict['ImageDocument']['Metadata']['HardwareSetting']['ParameterCollection'])[0]
    
    # Return the image data and the frame rate
    return im, frate

def get_frame_rate_targets(parameter_collection: list) -> list:
    """
    Extracts frame rate targets from a given parameter collection.

    This function iterates through the collection, checking for the presence of 'FrameRateTarget'.
    If 'FrameRateTarget' is found, it retrieves its value and adds it to the list of frame rate targets.

    Args:
        parameter_collectiom: A list of parameter items, each potentially containing a 'FrameRateTarget'.

    Returns:
        frame_rate_targets: A list of extracted frame rate targets.
    """
    frame_rate_targets = []
    
    for item in parameter_collection:
        if 'FrameRateTarget' in item:
            # Extract the frame rate target value
            frame_rate_target = item['FrameRateTarget'].get('#text', None)
            if frame_rate_target is not None:
                frame_rate_targets.append(frame_rate_target)
    
    return frame_rate_targets



