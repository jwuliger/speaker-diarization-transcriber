# Speaker Diarization Transcriber

Speaker Diarization Transcriber is a Python tool that leverages Google Cloud Speech-to-Text API to perform speaker diarization and transcription on audio files. It automatically identifies and separates different speakers in an audio file, providing a structured JSON output of the conversation.

## Features

- Speaker Diarization: Automatically identifies and labels different speakers in the audio.
- Transcription: Converts speech to text with high accuracy.
- Large File Support: Handles large audio files by utilizing Google Cloud Storage.
- Mono Conversion: Automatically converts stereo audio to mono when necessary.
- Flexible Input: Supports various audio formats compatible with the Google Cloud Speech-to-Text API.
- JSON Output: Provides a clean, structured JSON output for easy parsing and integration.

## Requirements

- Python 3.7+
- Google Cloud account with Speech-to-Text API enabled
- Google Cloud credentials (service account key)

## Installation

1. Clone this repository:
git clone https://github.com/jwuliger/speaker-diarization-transcriber.git
cd speaker-diarization-transcriber
2. Install dependencies:
poetry install
3. Set up Google Cloud credentials:
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

## Usage

1. Place your audio file in the `audio` directory.
2. Use the `SpeakerDiarizationTranscriber` class in your Python script:
from speaker_diarization import SpeakerDiarizationTranscriber
transcriber = SpeakerDiarizationTranscriber()
result = transcriber.perform_diarization("audio/your_audio_file.wav")
if result:
print(result)
else:
print("Diarization failed. Please check your audio file and try again.")
3. The transcription result will be printed to the console and saved as a JSON file in the `output` directory.
4. Check the `output` directory for the JSON file named `<input_filename>_transcription.json`.

## Configuration

You can customize the `SpeakerDiarizationTranscriber` by passing arguments to its constructor:

Here's the code formatted in Markdown:

```python
transcriber = SpeakerDiarizationTranscriber(
    min_speaker_count=2,
    max_speaker_count=10,
    language_code="en-US"
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Cloud Speech-to-Text API
- Pydub library for audio processing