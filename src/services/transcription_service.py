"""
Transcription Service for Speaker Diarization

This module provides a TranscriptionService class that handles the formatting and refinement
of transcription data obtained from speaker diarization.
"""


class TranscriptionService:
    """
    A service class for processing and refining transcription data from speaker diarization.
    """

    @staticmethod
    def format_transcription(words_info):
        """
        Format the diarization result into a structured list of speaker utterances.

        This method processes the word-level information from the diarization result,
        grouping words by speaker and handling question-answer scenarios.

        Args:
        words_info (list): List of word information objects from the diarization result.

        Returns:
        list: List of dictionaries containing speaker-grouped transcriptions with confidence scores.
        """
        transcript = []
        current_speaker = None
        current_utterance = []
        confidence_threshold = 0.8  # Confidence threshold for including words

        def add_current_utterance():
            if current_utterance:
                utterance_text = " ".join(
                    word["word"] for word in current_utterance
                ).strip()
                avg_confidence = sum(
                    word["confidence"] for word in current_utterance
                ) / len(current_utterance)

                # Split questions and answers
                if "?" in utterance_text:
                    question, answer = utterance_text.split("?", 1)
                    question += "?"

                    transcript.append(
                        {
                            "speaker": f"speaker {current_speaker}",
                            "text": question.strip(),
                            "avg_confidence": avg_confidence,
                        }
                    )

                    if answer.strip():
                        transcript.append(
                            {
                                # Switch speaker for the answer
                                "speaker": f"speaker {3 - current_speaker}",
                                "text": answer.strip(),
                                "avg_confidence": avg_confidence,
                            }
                        )
                else:
                    transcript.append(
                        {
                            "speaker": f"speaker {current_speaker}",
                            "text": utterance_text,
                            "avg_confidence": avg_confidence,
                        }
                    )

        for word_info in words_info:
            word = word_info.word
            speaker_tag = word_info.speaker_tag
            confidence = word_info.confidence

            # Check if we're starting a new speaker's utterance
            if speaker_tag != current_speaker:
                add_current_utterance()
                current_speaker = speaker_tag
                current_utterance = []

            # Add word to current utterance if confidence is above threshold
            if confidence >= confidence_threshold:
                current_utterance.append({"word": word, "confidence": confidence})

        # Add the last utterance
        add_current_utterance()

        return transcript

    @staticmethod
    def refine_speaker_tags(transcript):
        """
        Refine speaker tags by alternating speakers for consecutive utterances,
        ensuring questions and answers are attributed to different speakers.

        This method improves the accuracy of speaker attribution, especially
        in question-answer scenarios.

        Args:
        transcript (list): The original transcript with potentially incorrect speaker tags.

        Returns:
        list: The refined transcript with corrected speaker tags.
        """
        refined_transcript = []
        current_speaker = 1

        for i, utterance in enumerate(transcript):
            refined_utterance = utterance.copy()

            if utterance["text"].endswith("?"):
                refined_utterance["speaker"] = f"speaker {current_speaker}"
                refined_transcript.append(refined_utterance)
                # Switch to the other speaker for the answer
                current_speaker = 3 - current_speaker
            else:
                refined_utterance["speaker"] = f"speaker {current_speaker}"
                refined_transcript.append(refined_utterance)

                # Only switch speakers if the next utterance is not a continuation of the current one
                if i + 1 < len(transcript) and not transcript[i + 1]["text"].startswith(
                    ("and", "but", "or", "so")
                ):
                    current_speaker = 3 - current_speaker  # Alternate between 1 and 2

        return refined_transcript
