import whisper

from backend.config import settings


class TranscriptionService:
    _model: whisper.Whisper | None = None

    @classmethod
    def _get_model(cls) -> whisper.Whisper:
        if cls._model is None:
            cls._model = whisper.load_model(settings.whisper_model)
        return cls._model

    def transcribe(self, file_path: str) -> str:
        """Transcribe an audio/video file and return the full transcript text."""
        model = self._get_model()
        result = model.transcribe(file_path)
        return result["text"].strip()


transcription_service = TranscriptionService()
