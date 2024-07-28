"""
Speaker Diarization using Google Cloud Speech-to-Text API

This script defines a SpeakerDiarizationTranscriber class that performs speaker diarization
on an audio file using Google Cloud Speech-to-Text API.
It supports large audio files by uploading to Google Cloud Storage and using the long-running recognition method.
The audio is converted to mono if necessary, and the sample rate is automatically detected from the WAV file.
The output is a JSON-formatted transcription grouped by speakers, with normalized speaker labels,
which is both printed to the console and saved as a JSON file.
"""

import time
import os
import wave
import tempfile
import json
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
from google.api_core import exceptions
from pydub import AudioSegment


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
        self.language_code = language_code
        self.speech_client = speech.SpeechClient()
        self.storage_client = storage.Client()

    def get_wav_info(self, wav_file):
        """
        Get the sample rate and number of channels from a WAV file.

        Args:
        wav_file (str): Path to the WAV file.

        Returns:
        tuple: (sample_rate, channels)
        """
        with wave.open(wav_file, "rb") as wav:
            return wav.getframerate(), wav.getnchannels()

    def convert_to_mono(self, input_file, output_file):
        """
        Convert a stereo WAV file to mono.

        Args:
        input_file (str): Path to the input WAV file.
        output_file (str): Path to save the output mono WAV file.

        Returns:
        str: Path to the mono WAV file.
        """
        audio = AudioSegment.from_wav(input_file)
        mono_audio = audio.set_channels(1)
        mono_audio.export(output_file, format="wav")
        return output_file

    def format_transcription(self, words_info):
        """
        Format the diarization result into a JSON structure with normalized speaker labels.

        Args:
        words_info (list): List of word information from the diarization result.

        Returns:
        str: JSON formatted string of the transcription with normalized speaker labels.
        """
        transcript = []
        current_speaker = None
        current_transcription = ""
        speaker_map = {}
        next_speaker_id = 1

        for word_info in words_info:
            if word_info.speaker_tag not in speaker_map:
                speaker_map[word_info.speaker_tag] = next_speaker_id
                next_speaker_id += 1

            normalized_speaker = speaker_map[word_info.speaker_tag]

            if normalized_speaker != current_speaker:
                if current_speaker is not None:
                    transcript.append(
                        {
                            "speaker": current_speaker,
                            "transcription": current_transcription.strip(),
                        }
                    )
                current_speaker = normalized_speaker
                current_transcription = word_info.word + " "
            else:
                current_transcription += word_info.word + " "

        # Add the last speaker's transcription
        if current_speaker is not None:
            transcript.append(
                {
                    "speaker": current_speaker,
                    "transcription": current_transcription.strip(),
                }
            )

        # Combine consecutive entries from the same speaker
        combined_transcript = []
        for entry in transcript:
            if (
                combined_transcript
                and combined_transcript[-1]["speaker"] == entry["speaker"]
            ):
                combined_transcript[-1]["transcription"] += " " + \
                    entry["transcription"]
            else:
                combined_transcript.append(entry)

        return json.dumps(combined_transcript, indent=2)

    def perform_diarization(self, speech_file):
        """
        Perform speaker diarization on the given audio file.

        This method converts the audio to mono if necessary, uploads the audio file
        to a temporary Google Cloud Storage bucket, then uses the GCS URI to perform
        speaker diarization using the Google Cloud Speech-to-Text API.
        It supports large audio files by using the long-running recognition method.
        The sample rate is automatically detected from the WAV file.
        The result is saved as a JSON file in the 'output' directory.

        Args:
        speech_file (str): Path to the audio file to be processed.

        Returns:
        str: JSON formatted string of the transcription with normalized speaker labels, or None if an error occurred.
        """
        print(f"Processing file: {speech_file}")

        # Get the sample rate and number of channels from the WAV file
        sample_rate, channels = self.get_wav_info(speech_file)
        print(f"Detected sample rate: {sample_rate} Hz, Channels: {channels}")

        # Convert to mono if necessary
        if channels > 1:
            print("Converting audio to mono...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                mono_file = self.convert_to_mono(speech_file, temp_file.name)
            speech_file = mono_file
            print(f"Converted to mono: {speech_file}")

        # Create a unique bucket name
        bucket_name = f"temp-audio-bucket-{int(time.time())}"
        bucket = self.storage_client.create_bucket(bucket_name)

        # Upload the audio file to GCS
        blob_name = os.path.basename(speech_file)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(speech_file)

        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        print(f"Audio file uploaded to: {gcs_uri}")

        # Create RecognitionAudio object
        audio = speech.RecognitionAudio(uri=gcs_uri)

        # Configure speaker diarization
        diarization_config = speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=self.min_speaker_count,
            max_speaker_count=self.max_speaker_count,
        )

        # Configure recognition settings
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=self.language_code,
            diarization_config=diarization_config,
        )

        print("Sending request to Google Cloud Speech-to-Text API...")
        try:
            # Start long-running recognition operation
            operation = self.speech_client.long_running_recognize(
                config=config, audio=audio
            )

            print("\nProcessing audio. This may take several minutes for large files.")
            while not operation.done():
                print(".", end="", flush=True)
                time.sleep(5)  # Check status every 5 seconds

            print("\nProcessing complete!")

            response = operation.result()

            all_words = []
            for result in response.results:
                all_words.extend(result.alternatives[0].words)

            # Format the transcription with normalized speaker labels
            formatted_transcription = self.format_transcription(all_words)

            print("\nTranscription result:")
            print(formatted_transcription)

            # Save the transcription to a JSON file
            output_filename = (
                os.path.splitext(os.path.basename(speech_file))[0]
                + "_transcription.json"
            )
            output_path = os.path.join("output", output_filename)
            os.makedirs("output", exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(json.loads(formatted_transcription), f, indent=2)
            print(f"\nTranscription saved to {output_path}")

            return formatted_transcription

        except exceptions.GoogleAPICallError as e:
            print(f"\nError occurred: {e}")
            return None
        finally:
            # Clean up: delete the GCS bucket and its contents
            bucket.delete(force=True)
            print(f"Temporary GCS bucket {bucket_name} deleted.")

            # Remove temporary mono file if it was created
            if channels > 1 and os.path.exists(mono_file):
                os.remove(mono_file)
                print(f"Temporary mono file deleted: {mono_file}")


if __name__ == "__main__":
    # Specify the path to your audio file
    speech_file = "audio/conversation.wav"

    # Create an instance of SpeakerDiarizationTranscriber
    transcriber = SpeakerDiarizationTranscriber()

    # Perform diarization
    result = transcriber.perform_diarization(speech_file)

    if result:
        print("\nFull transcription result:")
        print(result)
    else:
        print("Diarization failed. Please check your audio file and try again.")
