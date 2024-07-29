"""
Audio Service for Speaker Diarization

This module provides an AudioService class that handles audio file operations
such as getting WAV file information and converting stereo to mono.
"""

import wave
from pydub import AudioSegment


class AudioService:
    """
    A service class for handling audio file operations.
    """

    @staticmethod
    def get_wav_info(wav_file):
        """
        Get the sample rate and number of channels from a WAV file.

        Args:
        wav_file (str): Path to the WAV file.

        Returns:
        tuple: (sample_rate, channels)
        """
        with wave.open(wav_file, "rb") as wav:
            return wav.getframerate(), wav.getnchannels()

    @staticmethod
    def convert_to_mono(input_file, output_file):
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
