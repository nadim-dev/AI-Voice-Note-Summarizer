import threading
import wave

import numpy as np
import sounddevice as sd


class RecordingSession:
    def __init__(
        self,
        sample_rate=16000,
        silence_threshold=0.015,
        silence_duration=1.5,
        min_record_seconds=1.0,
        max_record_seconds=120.0,
        block_duration=0.2,
    ):
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.min_record_seconds = min_record_seconds
        self.max_record_seconds = max_record_seconds
        self.block_duration = block_duration

        self._stop_event = threading.Event()
        self._cancel_event = threading.Event()
        self._done_event = threading.Event()
        self._thread = None

        self.audio = None
        self.error = None
        self.canceled = False
        self.speech_detected = False
        self.status = "idle"

    def start(self):
        self.status = "recording"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop_event.set()

    def cancel(self):
        self._cancel_event.set()
        self.canceled = True
        self.status = "cancelled"

    def is_finished(self):
        return self._done_event.is_set()

    def _run(self):
        block_size = int(self.sample_rate * self.block_duration)
        silence_blocks_to_stop = max(1, int(self.silence_duration / self.block_duration))
        min_blocks_before_stop = max(1, int(self.min_record_seconds / self.block_duration))
        max_blocks = max(1, int(self.max_record_seconds / self.block_duration))

        audio_chunks = []
        silent_blocks = 0

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=block_size,
            ) as stream:
                for block_index in range(max_blocks):
                    if self._cancel_event.is_set():
                        self.canceled = True
                        self.status = "cancelled"
                        break

                    chunk, _overflowed = stream.read(block_size)
                    chunk = np.copy(chunk)
                    audio_chunks.append(chunk)

                    volume = float(np.sqrt(np.mean(np.square(chunk))))
                    if volume >= self.silence_threshold:
                        self.speech_detected = True
                        self.status = "speech_detected"
                        silent_blocks = 0
                    elif self.speech_detected:
                        silent_blocks += 1

                    should_stop_for_silence = (
                        self.speech_detected
                        and block_index >= min_blocks_before_stop
                        and silent_blocks >= silence_blocks_to_stop
                    )
                    should_stop_manually = (
                        self._stop_event.is_set() and block_index >= min_blocks_before_stop
                    )

                    if should_stop_for_silence or should_stop_manually:
                        self.status = "processing"
                        break

            if self.canceled:
                return

            if not audio_chunks:
                raise RuntimeError("No audio captured from microphone.")

            if not self.speech_detected:
                raise RuntimeError(
                    "No speech detected. Please try speaking closer to the microphone."
                )

            self.audio = np.concatenate(audio_chunks, axis=0)
            self.status = "completed"
        except Exception as exc:
            self.error = str(exc)
            self.status = "error"
        finally:
            self._done_event.set()


class AudioRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

    def start_recording_session(self):
        return RecordingSession(sample_rate=self.sample_rate).start()

    def save_to_file(self, audio_data, filename="recording.wav"):
        audio_int16 = (audio_data * 32767).astype(np.int16)

        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return filename
