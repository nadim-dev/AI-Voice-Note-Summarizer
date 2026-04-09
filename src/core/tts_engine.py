import os
from datetime import datetime

from gtts import gTTS


class TTSEngine:
    def __init__(self, lang="en", tld="com", slow=False):
        self.lang = lang
        self.tld = tld
        self.slow = slow

    def text_to_speech(self, text, filename=None):
        if not filename:
            filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"

        try:
            tts = gTTS(text=text, lang=self.lang, tld=self.tld, slow=self.slow)
            tts.save(filename)
            return filename
        except Exception:
            return None

    def read_audio_bytes(self, filename):
        try:
            with open(filename, "rb") as audio_file:
                return audio_file.read()
        except OSError:
            return None

    def cleanup(self, filename):
        try:
            if os.path.exists(filename):
                os.unlink(filename)
        except OSError:
            pass
