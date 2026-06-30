import whisper

class AudioProcessor:
    def __init__(self, config, memory):
        self.config = config
        self.model = whisper.load_model(config['audio']['whisper_model'])
        self.memory = memory
    
    def transcribe(self, audio_data):
        """Transcribe with Whisper."""
        try:
            # Force fp16=False to avoid Categorical logits NaN crashes, and language='en' to eliminate foreign hallucinations
            result = self.model.transcribe(audio_data, fp16=False, language="en")
            return result.get("text", "").strip()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Whisper transcription error: {e}")
            return ""