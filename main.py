"""
Speaker Diarization Transcriber

This script defines a SpeakerDiarizationTranscriber class that performs speaker diarization
on an audio file using Google Cloud Speech-to-Text API.
It supports large audio files by uploading to Google Cloud Storage and using the long-running recognition method.
The audio is converted to mono if necessary, and the sample rate is automatically detected from the WAV file.
The output is a list of words with their corresponding speaker tags and confidence scores, which is both printed to the console
and saved as a JSON file. An additional JSON file with chronologically ordered speaker-grouped transcriptions is also saved.
It also implements caching of the raw API response to reduce costs during development and testing.
"""

import os
import time
import json
import tempfile
from src.services.audio_service import AudioService
from src.services.cloud_storage_service import CloudStorageService
from src.services.speech_to_text_service import SpeechToTextService
from src.services.transcription_service import TranscriptionService
from src.services.cache_service import CacheService
from src.utils.file_utils import save_json


class SpeakerDiarizationTranscriber:
    def __init__(
        self, min_speaker_count=2, max_speaker_count=10, language_code="en-US"
    ):
        """
        Initialize the SpeakerDiarizationTranscriber.

        Args:
        min_speaker_count (int): Minimum number of speakers to detect.
        max_speaker_count (int): Maximum number of speakers to detect.
        language_code (str): Language code for speech recognition.
        """
        self.min_speaker_count = min_speaker_count
        self.max_speaker_count = max_speaker_count
        self.audio_service = AudioService()
        self.cloud_storage_service = CloudStorageService()
        self.speech_to_text_service = SpeechToTextService(language_code)
        self.transcription_service = TranscriptionService()
        self.cache_service = CacheService()

    def perform_diarization(self, speech_file, use_cache=True):
        """
        Perform speaker diarization on the given audio file.

        This method first checks for a cached result. If not found or if use_cache is False,
        it converts the audio to mono if necessary, uploads the audio file to a temporary
        Google Cloud Storage bucket, then uses the GCS URI to perform speaker diarization
        using the Google Cloud Speech-to-Text API.
        It supports large audio files by using the long-running recognition method.
        The sample rate is automatically detected from the WAV file.
        The result is saved as two JSON files in the 'output' directory.

        Args:
        speech_file (str): Path to the audio file to be processed.
        use_cache (bool): Whether to use cached results if available.

        Returns:
        tuple: (word_level_output, speaker_level_output)
        """
        print(f"Processing file: {speech_file}")
        print(f"Full path of speech file: {os.path.abspath(speech_file)}")

        original_filename = os.path.basename(speech_file)

        # Check for cached result
        if use_cache:
            cached_response = self.cache_service.load_cache(original_filename)
            if cached_response:
                print("Using cached API response.")
                return self._process_response(cached_response, original_filename)

        # Get the sample rate and number of channels from the WAV file
        sample_rate, channels = self.audio_service.get_wav_info(speech_file)
        print(f"Detected sample rate: {sample_rate} Hz, Channels: {channels}")

        # Convert to mono if necessary
        if channels > 1:
            print("Converting audio to mono...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                speech_file = self.audio_service.convert_to_mono(
                    speech_file, temp_file.name)
            print(f"Converted to mono: {speech_file}")

        # Create a unique bucket name
        bucket_name = f"temp-audio-bucket-{int(time.time())}"
        blob_name = os.path.basename(speech_file)

        try:
            # Upload the audio file to GCS
            gcs_uri = self.cloud_storage_service.upload_file(
                speech_file, bucket_name, blob_name)
            print(f"Audio file uploaded to: {gcs_uri}")

            # Perform transcription
            response = self.speech_to_text_service.transcribe_audio(
                gcs_uri, sample_rate, self.min_speaker_count, self.max_speaker_count
            )

            # Cache the response
            self.cache_service.save_cache(original_filename, response)

            return self._process_response(response, original_filename)

        finally:
            # Clean up: delete the GCS bucket and its contents
            self.cloud_storage_service.delete_bucket(bucket_name)

            # Remove temporary mono file if it was created
            if channels > 1 and os.path.exists(speech_file):
                os.remove(speech_file)
                print(f"Temporary mono file deleted: {speech_file}")

    def _process_response(self, response, original_filename):
        """
        Process the API response and generate output files.

        Args:
        response: The API response object.
        original_filename (str): The original filename of the processed audio.

        Returns:
        tuple: (word_level_output, refined_speaker_level_output)
        """
        result = response.results[-1]
        words_info = result.alternatives[0].words

        # Prepare the word-level output
        word_level_output = [
            {
                "word": word_info.word,
                "speaker_tag": word_info.speaker_tag,
                "confidence": word_info.confidence,
            }
            for word_info in words_info
        ]

        # Prepare the speaker-level output
        speaker_level_output = self.transcription_service.format_transcription(
            words_info)

        # Refine speaker tags
        refined_speaker_level_output = self.transcription_service.refine_speaker_tags(
            speaker_level_output)

        # Save the word-level output to a JSON file
        word_output_filename = f"{os.path.splitext(original_filename)[0]}_word_level_transcription.json"
        save_json(word_level_output, word_output_filename)

        # Save the refined speaker-level output to a JSON file
        speaker_output_filename = f"{os.path.splitext(original_filename)[0]}_speaker_level_transcription.json"
        save_json(refined_speaker_level_output, speaker_output_filename)

        return word_level_output, refined_speaker_level_output


if __name__ == "__main__":
    # Specify the path to your audio file
    speech_file = "audio/conversation.wav"

    # Create an instance of SpeakerDiarizationTranscriber
    transcriber = SpeakerDiarizationTranscriber()

    # Perform diarization
    word_result, speaker_result = transcriber.perform_diarization(
        speech_file, use_cache=True)

    if word_result and speaker_result:
        print("\nFull word-level transcription result:")
        print(json.dumps(word_result, indent=2))
        print("\nFull refined speaker-level transcription result:")
        print(json.dumps(speaker_result, indent=2))
    else:
        print("Diarization failed. Please check your audio file and try again.")
