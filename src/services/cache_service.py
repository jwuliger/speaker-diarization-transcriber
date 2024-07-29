"""
Cache Service for Speaker Diarization

This module provides a CacheService class that handles caching of API responses
to reduce costs during development and testing.
"""

import os
import pickle


class CacheService:
    """
    A service class for caching API responses.
    """

    def __init__(self, cache_dir="cache"):
        """
        Initialize the CacheService.

        Args:
        cache_dir (str): Directory to store cache files.
        """
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def save_cache(self, filename, response):
        """
        Save the API response to a cache file.

        Args:
        filename (str): Name of the original audio file.
        response: The API response object to cache.
        """
        cache_file = os.path.join(self.cache_dir, f"{filename}.pickle")
        with open(cache_file, "wb") as f:
            pickle.dump(response, f)
        print(f"Cache saved to: {cache_file}")

    def load_cache(self, filename):
        """
        Load the API response from a cache file if it exists.

        Args:
        filename (str): Name of the original audio file.

        Returns:
        The cached API response object if it exists, None otherwise.
        """
        cache_file = os.path.join(self.cache_dir, f"{filename}.pickle")
        print(f"Looking for cache file: {cache_file}")
        if os.path.exists(cache_file):
            print(f"Cache file found: {cache_file}")
            try:
                with open(cache_file, "rb") as f:
                    cached_data = pickle.load(f)
                print("Cache file successfully loaded.")
                return cached_data
            except Exception as e:
                print(f"Error loading cache file: {e}")
        else:
            print(f"Cache file not found: {cache_file}")
        return None
