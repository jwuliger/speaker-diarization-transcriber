"""
Speech-to-Text Service for Speaker Diarization

This module provides a SpeechToTextService class that handles the interaction
with Google Cloud Speech-to-Text API for transcription and diarization.
"""

from google.cloud import speech_v1p1beta1 as speech
from google.api_core import exceptions


class SpeechToTextService:
    """
    A service class for handling Google Cloud Speech-to-Text API operations.
    """

    def __init__(self, language_code="en-US"):
        """
        Initialize the SpeechToTextService.

        Args:
        language_code (str): The language code for speech recognition.
        """
        self.speech_client = speech.SpeechClient()
        self.language_code = language_code

    def transcribe_audio(
        self, gcs_uri, sample_rate, min_speaker_count, max_speaker_count
    ):
        """
        Transcribe audio using Google Cloud Speech-to-Text API with speaker diarization.

        Args:
        gcs_uri (str): Google Cloud Storage URI of the audio file.
        sample_rate (int): Sample rate of the audio file.
        min_speaker_count (int): Minimum number of speakers to detect.
        max_speaker_count (int): Maximum number of speakers to detect.

        Returns:
        The API response containing the transcription and diarization results.

        Raises:
        exceptions.GoogleAPICallError: If an error occurs during the API call.
        """
        audio = speech.RecognitionAudio(uri=gcs_uri)
        config = self._get_recognition_config(
            sample_rate, min_speaker_count, max_speaker_count
        )

        print("Sending request to Google Cloud Speech-to-Text API...")
        try:
            operation = self.speech_client.long_running_recognize(
                config=config, audio=audio
            )

            print("\nProcessing audio. This may take several minutes for large files.")
            while not operation.done():
                print(".", end="", flush=True)
                operation.poll()  # This will sleep for the default polling interval

            print("\nProcessing complete!")

            return operation.result()

        except exceptions.GoogleAPICallError as e:
            print(f"\nError occurred: {e}")
            raise

    def _get_recognition_config(
        self, sample_rate, min_speaker_count, max_speaker_count
    ):
        """
        Create the recognition config for the Speech-to-Text API.

        Args:
        sample_rate (int): Sample rate of the audio file.
        min_speaker_count (int): Minimum number of speakers to detect.
        max_speaker_count (int): Maximum number of speakers to detect.

        Returns:
        speech.RecognitionConfig: The configuration for the API request.
        """
        diarization_config = speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=min_speaker_count,
            max_speaker_count=max_speaker_count,
        )

        return speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=self.language_code,
            diarization_config=diarization_config,
            enable_word_confidence=True,
        )
