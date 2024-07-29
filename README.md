# Speaker Diarization Transcriber

Speaker Diarization Transcriber is a Python tool that leverages Google Cloud Speech-to-Text API to perform speaker diarization and transcription on audio files. It automatically identifies and separates different speakers in an audio file, providing a structured JSON output of the conversation, with improved handling of question-answer scenarios.

Features

-   Speaker Diarization: Automatically identifies and labels different speakers in the audio.
-   Transcription: Converts speech to text with high accuracy.
-   Question-Answer Handling: Intelligently separates questions and answers, attributing them to different speakers.
-   Large File Support: Handles large audio files by utilizing Google Cloud Storage.
-   Mono Conversion: Automatically converts stereo audio to mono when necessary.
-   Flexible Input: Supports various audio formats compatible with the Google Cloud Speech-to-Text API
-   JSON Output: Provides clean, structured JSON outputs for both word-level and speaker-level transcriptions.
-   Caching: Implements result caching to reduce API calls during development and testing.

Requirements

-   Python 3.7+
-   Poetry for dependency management
-   Google Cloud account with Speech-to-Text API enabled
-   Google Cloud credentials (service account key)

Installation

1. Clone this repository:
   git clone https://github.com/jwuliger/speaker-diarization-transcriber.git
   cd speaker-diarization-transcriber
2. Install dependencies using Poetry:
   poetry install
3. Set up Google Cloud credentials:
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

Usage

1. Place your audio file in the 'audio' directory.
2. Run the main script using Poetry:

```python
poetry run python main.py
```

1. The transcription results will be printed to the console and saved as JSON files in the 'output' directory:
    - <input_filename>\_word_level_transcription.json: Contains word-level transcription with speaker tags and confidence scores.
    - <input_filename>\_speaker_level_transcription.json: Contains refined speaker-level transcription with improved question-answer handling.

Configuration

You can customize the SpeakerDiarizationTranscriber by modifying the parameters in main.py:

```python
transcriber = SpeakerDiarizationTranscriber(
    min_speaker_count=2,
    max_speaker_count=10,
    language_code="en-US"
)
```

Caching

The tool implements caching to reduce API calls during development and testing. By default, caching is enabled. To disable caching, modify the use_cache parameter when calling perform_diarization:

```python
word_result, speaker_result = transcriber.perform_diarization("audio/your_audio_file.wav", use_cache=False)
```

Cache files are stored in the 'cache' directory and named after the original audio file.

Project Structure

```plaintext
speaker_diarization_transcriber/
├── main.py
├── src/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio_service.py
│   │   ├── cloud_storage_service.py
│   │   ├── speech_to_text_service.py
│   │   ├── transcription_service.py
│   │   └── cache_service.py
│   └── utils/
│       ├── __init__.py
│       └── file_utils.py
├── audio/
│   └── conversation.wav
├── output/
├── cache/
├── pyproject.toml
└── README.md
```

Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

License

This project is licensed under the MIT License - see the LICENSE file for details.

Acknowledgments

-   Google Cloud Speech-to-Text API
-   Pydub library for audio processing
-   Poetry for dependency management
