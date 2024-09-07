import re
import logging
import xml.etree.ElementTree as ET
import tifffile

def load_image_data_moldev(fname: str) -> tuple:
    """
    Loads image data from a Tiff file captured on a Molecular Devices instrument
    and extracts the frame rate.
    
    Args:
        fname: The file path of the Tiff file to be loaded.
    
    Returns:
        A tuple containing the image data and the frame rate.
           - im: The image data read from the Tiff file.
           - frate: The frame rate extracted from the metadata.
    """
    # Read the image data from the file
    im = tifffile.imread(fname)
    
    # Load metadata from the Tiff file
    metadata = load_tiff_metadata(fname)
    root = ET.fromstring(metadata['ImageDescription'])
    description = get_metadata_value(root, 'Description')
    frate, exposure_units = extract_exposure(description)

    # Check and print a warning if exposure units are not in msec
    if exposure_units != 'msec':
        print(f"Warning: Exposure units for file {fname} are '{exposure_units}', not 'msec'.")

    # Return the image data and the frame rate
    return im, frate

def load_tiff_metadata(file_path):
    """
    Loads metadata from a TIFF file.
    
    Args:
    file_path (str): The path to the TIFF file.
    
    Returns:
    dict: A dictionary containing the metadata of the first page of the TIFF file.
    """
    with tifffile.TiffFile(file_path) as tif:
        # Assuming the metadata is stored in the first page
        page = tif.pages[0]
        # Extract metadata tags
        metadata = {tag.name: tag.value for tag in page.tags.values()}
    return metadata

def get_metadata_value(root, prop_id):
    """
    Retrieves the value of a queried property from an XML metadata root element.
    
    Args:
    root (xml.etree.ElementTree.Element): The root element of the XML metadata.
    prop_id (str): The ID of the property to retrieve.
    
    Returns:
    str: The value of the specified property, or None if the property is not found.
    """
    for prop in root.iter('prop'):
        if prop.get('id') == prop_id:
            return prop.get('value')
    return None

def extract_exposure(description):
    """
    Extracts the exposure time and units from a description string.
    
    Args:
    description (str): The description string containing the exposure information.
    
    Returns:
    tuple: A tuple containing the exposure time (float) and units (str), or None if not found.
    """
    if description:
        # Split the description into separate lines
        lines = description.split('\r\n')
        # Iterate over each line to find the exposure time
        for line in lines:
            if 'Exposure:' in line:
                # Assuming the format is 'Exposure: X msec'
                exposure = line.split(': ')[1].strip()
                exposure_time = float(exposure.split(' ')[0])
                exposure_units = exposure.split(' ')[1]
                return exposure_time, exposure_units
    return None

def load_image_data_moldev_concat(fname: str) -> tuple:
    """
    Loads image data from a Tiff file captured on a Molecular Devices instrument
    and extracts the frame rate. This is for any file thats been concatenated
    
    Args:
    fname: The file path of the Tiff file to be loaded.
    
    Returns:
    tuple: A tuple containing the image data and the frame rate.
           - im: The image data read from the Tiff file.
           - frate: The frame rate extracted from the metadata.
    """
    # Read the image data from the file
    im = tifffile.imread(fname)
    
    # Load metadata from the Tiff file
    metadata = load_tiff_metadata(fname)
    image_description = metadata.get('ImageDescription')

    # Extract the exposure information from the image description
    exposure_units,frate = None,None
    if image_description:
        # Extract the inner XML content
        match = re.search(r'<prop id=\\"Description\\" type=\\"string\\" value=\\"([^"]+)\\"', image_description)
        if match:
            description = match.group(1)
            # Search for the exposure information
            exposure_match = re.search(r'Exposure: (\d+(\.\d+)?)(\s*(msec|sec|ms|s))', description, re.IGNORECASE)
            if exposure_match:
                frate = int(exposure_match.group(1))
                exposure_units = exposure_match.group(4)

    # Raise an error if exposure information is not found
    if exposure_units is None or frate is None:
        raise ValueError(f"Exposure information not found in metadata for file {fname}.")

    # Check and print a warning if exposure units are not in msec
    if exposure_units.lower() not in ['msec', 'ms']:
        logging.warning(f"Exposure units for file {fname} are '{exposure_units}', not 'msec'.")

    # Return the image data and the frame rate
    return im, frate