"""
Cloud Storage Service for Speaker Diarization

This module provides a CloudStorageService class that handles operations
related to Google Cloud Storage, such as uploading files and managing buckets.
"""

from google.cloud import storage


class CloudStorageService:
    """
    A service class for handling Google Cloud Storage operations.
    """

    def __init__(self):
        """
        Initialize the CloudStorageService.
        """
        self.storage_client = storage.Client()

    def upload_file(self, local_file_path, bucket_name, blob_name):
        """
        Upload a file to Google Cloud Storage.

        Args:
        local_file_path (str): Path to the local file to upload.
        bucket_name (str): Name of the GCS bucket.
        blob_name (str): Name to give the file in GCS.

        Returns:
        str: GCS URI of the uploaded file.
        """
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file_path)
        return f"gs://{bucket_name}/{blob_name}"

    def delete_bucket(self, bucket_name):
        """
        Delete a Google Cloud Storage bucket and all its contents.

        Args:
        bucket_name (str): Name of the GCS bucket to delete.
        """
        bucket = self.storage_client.bucket(bucket_name)
        bucket.delete(force=True)
        print(f"Bucket {bucket_name} and all its contents have been deleted.")
