import whisper
import tempfile
import os

class TranscriptionEngine:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.model = None
    
    def load_model(self):
        if self.model is None:
            self.model = whisper.load_model(self.model_size)
        return self.model
    
    def transcribe_file(self, audio_path):
        model = self.load_model()
        result = model.transcribe(audio_path)
        return {
            'text': result['text'],
            'language': result.get('language', 'en')
        }
    
    def transcribe_uploaded(self, uploaded_file):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        result = self.transcribe_file(tmp_path)
        os.unlink(tmp_path)
        return result