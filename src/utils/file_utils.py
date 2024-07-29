"""
File Utilities for Speaker Diarization

This module provides utility functions for file operations,
such as saving JSON data to files.
"""

import os
import json


def save_json(data, filename, directory="output"):
    """
    Save data as a JSON file in the specified directory.

    Args:
    data: The data to be saved as JSON.
    filename (str): The name of the file to save.
    directory (str): The directory to save the file in. Default is "output".

    Returns:
    str: The full path of the saved file.

    Raises:
    IOError: If there's an error writing to the file.
    """
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"JSON data saved to {filepath}")
        return filepath
    except IOError as e:
        print(f"Error saving JSON data to {filepath}: {e}")
        raise
