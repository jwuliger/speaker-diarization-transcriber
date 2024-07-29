"""
Speaker Diarization using Google Cloud Speech-to-Text API

This script defines a SpeakerDiarizationTranscriber class that performs speaker diarization
on an audio file using Google Cloud Speech-to-Text API.
It supports large audio files by uploading to Google Cloud Storage and using the long-running recognition method.
The audio is converted to mono if necessary, and the sample rate is automatically detected from the WAV file.
The output is a list of words with their corresponding speaker tags and confidence scores, which is both printed to the console
and saved as a JSON file. An additional JSON file with chronologically ordered speaker-grouped transcriptions is also saved.
It also implements caching of the raw API response to reduce costs during development and testing.
"""

import time
import os
import wave
import tempfile
import json
import pickle
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
        Format the diarization result into a JSON structure with chronologically ordered speaker utterances.

        Args:
        words_info (list): List of word information from the diarization result.

        Returns:
        list: List of dictionaries containing speaker-grouped transcriptions with confidence scores.
        """
        transcript = []
        current_speaker = None
        current_utterance = []
        confidence_threshold = 0.8  # Confidence threshold for including words

        for word_info in words_info:
            word = word_info.word
            speaker_tag = word_info.speaker_tag
            confidence = word_info.confidence

            # Handle punctuation
            if word in ".,!?":
                if current_utterance:
                    current_utterance[-1]["word"] += word
                continue

            # Check if we're starting a new speaker's utterance
            if speaker_tag != current_speaker:
                if current_utterance:
                    self.add_utterance_to_transcript(
                        transcript, current_speaker, current_utterance
                    )
                current_speaker = speaker_tag
                current_utterance = []

            # Add word to current utterance if confidence is above threshold
            if confidence >= confidence_threshold:
                current_utterance.append({"word": word, "confidence": confidence})

        # Add the last utterance
        if current_utterance:
            self.add_utterance_to_transcript(
                transcript, current_speaker, current_utterance
            )

        return transcript

    def add_utterance_to_transcript(self, transcript, speaker, utterance):
        """
        Add an utterance to the transcript for a specific speaker.

        Args:
        transcript (list): The transcript list to update.
        speaker (int): The speaker tag.
        utterance (list): List of dictionaries containing words and their confidence scores.
        """
        utterance_text = " ".join(word_info["word"] for word_info in utterance)
        avg_confidence = (
            sum(word_info["confidence"] for word_info in utterance) / len(utterance)
            if utterance
            else 0
        )

        transcript.append(
            {
                "speaker": f"speaker {speaker}",
                "text": utterance_text,
                "avg_confidence": avg_confidence,
            }
        )

    def refine_speaker_tags(self, transcript):
        """
        Refine speaker tags by alternating speakers for consecutive utterances.

        Args:
        transcript (list): The original transcript with potentially incorrect speaker tags.

        Returns:
        list: The refined transcript with corrected speaker tags.
        """
        refined_transcript = []
        current_speaker = 1

        for utterance in transcript:
            refined_utterance = utterance.copy()
            refined_utterance["speaker"] = f"speaker {current_speaker}"
            refined_transcript.append(refined_utterance)
            current_speaker = 3 - current_speaker  # Alternate between 1 and 2

        return refined_transcript

    def save_cache(self, speech_file, response):
        """
        Save the API response to a cache file.

        Args:
        speech_file (str): Path to the original audio file.
        response: The API response object to cache.
        """
        cache_dir = "cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{os.path.basename(speech_file)}.pickle")
        with open(cache_file, "wb") as f:
            pickle.dump(response, f)

    def load_cache(self, speech_file):
        """
        Load the API response from a cache file if it exists.

        Args:
        speech_file (str): Path to the original audio file.

        Returns:
        The cached API response object if it exists, None otherwise.
        """
        cache_file = os.path.join("cache", f"{os.path.basename(speech_file)}.pickle")
        if os.path.exists(cache_file):
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return None

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

        # Check for cached result
        if use_cache:
            cached_response = self.load_cache(speech_file)
            if cached_response:
                print("Using cached API response.")
                response = cached_response
            else:
                print("No cached response found. Proceeding with API call.")
        else:
            print("Cache use disabled. Proceeding with API call.")

        if not use_cache or not cached_response:
            # Get the sample rate and number of channels from the WAV file
            sample_rate, channels = self.get_wav_info(speech_file)
            print(f"Detected sample rate: {sample_rate} Hz, Channels: {channels}")

            # Convert to mono if necessary
            if channels > 1:
                print("Converting audio to mono...")
                with tempfile.NamedTemporaryFile(
                    suffix=".wav", delete=False
                ) as temp_file:
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
                enable_word_confidence=True,  # Enable word confidence scores
            )

            print("Sending request to Google Cloud Speech-to-Text API...")
            try:
                # Start long-running recognition operation
                operation = self.speech_client.long_running_recognize(
                    config=config, audio=audio
                )

                print(
                    "\nProcessing audio. This may take several minutes for large files."
                )
                while not operation.done():
                    print(".", end="", flush=True)
                    time.sleep(5)  # Check status every 5 seconds

                print("\nProcessing complete!")

                response = operation.result()

                # Cache the response
                self.save_cache(speech_file, response)

            except exceptions.GoogleAPICallError as e:
                print(f"\nError occurred: {e}")
                return None, None
            finally:
                # Clean up: delete the GCS bucket and its contents
                bucket.delete(force=True)
                print(f"Temporary GCS bucket {bucket_name} deleted.")

                # Remove temporary mono file if it was created
                if channels > 1 and os.path.exists(mono_file):
                    os.remove(mono_file)
                    print(f"Temporary mono file deleted: {mono_file}")

        # Process the response (cached or new)
        result = response.results[-1]
        words_info = result.alternatives[0].words

        # Prepare the word-level output
        word_level_output = []
        for word_info in words_info:
            word_level_output.append(
                {
                    "word": word_info.word,
                    "speaker_tag": word_info.speaker_tag,
                    "confidence": word_info.confidence,
                }
            )

        # Prepare the speaker-level output
        speaker_level_output = self.format_transcription(words_info)

        # Refine speaker tags
        refined_speaker_level_output = self.refine_speaker_tags(speaker_level_output)

        # Print the word-level output
        print("\nWord-level transcription result:")
        for item in word_level_output:
            print(
                f"word: '{item['word']}', speaker_tag: {item['speaker_tag']}, confidence: {item['confidence']:.2f}"
            )

        # Print the refined speaker-level output
        print("\nRefined speaker-level transcription result:")
        print(json.dumps(refined_speaker_level_output, indent=2))

        # Save the word-level output to a JSON file
        word_output_filename = (
            os.path.splitext(os.path.basename(speech_file))[0]
            + "_word_level_transcription.json"
        )
        word_output_path = os.path.join("output", word_output_filename)
        os.makedirs("output", exist_ok=True)
        with open(word_output_path, "w") as f:
            json.dump(word_level_output, f, indent=2)
        print(f"\nWord-level transcription saved to {word_output_path}")

        # Save the refined speaker-level output to a JSON file
        speaker_output_filename = (
            os.path.splitext(os.path.basename(speech_file))[0]
            + "_speaker_level_transcription.json"
        )
        speaker_output_path = os.path.join("output", speaker_output_filename)
        with open(speaker_output_path, "w") as f:
            json.dump(refined_speaker_level_output, f, indent=2)
        print(f"Refined speaker-level transcription saved to {speaker_output_path}")

        return word_level_output, refined_speaker_level_output


if __name__ == "__main__":
    # Specify the path to your audio file
    speech_file = "audio/conversation.wav"

    # Create an instance of SpeakerDiarizationTranscriber
    transcriber = SpeakerDiarizationTranscriber()

    # Perform diarization
    word_result, speaker_result = transcriber.perform_diarization(
        speech_file, use_cache=True
    )

    if word_result and speaker_result:
        print("\nFull word-level transcription result:")
        print(json.dumps(word_result, indent=2))
        print("\nFull refined speaker-level transcription result:")
        print(json.dumps(speaker_result, indent=2))
    else:
        print("Diarization failed. Please check your audio file and try again.")
