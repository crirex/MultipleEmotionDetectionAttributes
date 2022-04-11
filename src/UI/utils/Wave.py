import wave
import librosa


class Wave:
    def __init__(self, channels=1, sample_width=2, frame_rate=16000):
        self._channels = channels
        self._sample_width = sample_width
        self._frame_rate = frame_rate

    def write_wave(self, fileName: str, data: []):
        if data is None or len(data) == 0:
            return

        wf = wave.open(fileName, "w")
        wf.setnchannels(self._channels)
        wf.setsampwidth(self._sample_width)
        wf.setframerate(self._frame_rate)
        wf.writeframes(b''.join(data))
        wf.close()

    def load_wave(self, filename, sample_rate=16000):
        y, sr = librosa.core.load(filename, sr=sample_rate, offset=0.5)
        return y, sr
