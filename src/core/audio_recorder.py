import sounddevice as sd
import numpy as np
import wave

class AudioRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
    
    def record(self, duration=30):
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        return audio, self.sample_rate
    
    def save_to_file(self, audio_data, filename="recording.wav"):
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        return filename