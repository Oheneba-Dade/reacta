from backend.config import settings


class TranscriptionService:
    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            import whisper
            cls._model = whisper.load_model(settings.whisper_model, download_root="/app/models")
        return cls._model

    def transcribe(self, file_path: str) -> str:
        """Transcribe an audio/video file and return the full transcript text."""
        model = self._get_model()
        result = model.transcribe(file_path)
        return result["text"].strip()


transcription_service = TranscriptionService()
