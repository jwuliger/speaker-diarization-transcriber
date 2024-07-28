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
git clone https://github.com/yourusername/speaker-diarization-transcriber.git
cd speaker-diarization-transcriber
2. Install dependencies:
poetry install
3. Set up Google Cloud credentials:
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

## Usage

1. Place your audio file in the `audio` directory.
2. Run the script:
python speaker_diarization.py
3. The transcription result will be printed to the console and saved as a JSON file in the `output` directory.

## Configuration

You can modify the following parameters in `speaker_diarization.py`:

- `min_speaker_count` and `max_speaker_count` in the `diarization_config`
- `language_code` in the `config` object

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Cloud Speech-to-Text API
- Pydub library for audio processing