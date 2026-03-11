from gtts import gTTS
import os
from datetime import datetime

class TTSEngine:
    def __init__(self, lang='en'):
        self.lang = lang
    
    def text_to_speech(self, text, filename=None):
        if not filename:
            filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        
        try:
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(filename)
            return filename
        except:
            return None
    
    def cleanup(self, filename):
        try:
            if os.path.exists(filename):
                os.unlink(filename)
        except:
            pass