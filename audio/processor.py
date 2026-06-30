import whisper

class AudioProcessor:
    def __init__(self, config, memory):
        self.config = config
        self.model = whisper.load_model(config['audio']['whisper_model'])
        self.memory = memory
    
    def transcribe(self, audio_data):
        """Transcribe with Whisper."""
        result = self.model.transcribe(audio_data)
        return result["text"]