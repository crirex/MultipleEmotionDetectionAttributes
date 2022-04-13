import io
import wave
import librosa


class WaveUtils:
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
        return librosa.core.load(filename, sr=sample_rate, offset=0.5)

    def convert_to_wave(self, data):
        with io.BytesIO() as wav_file:
            wav_writer = wave.open(wav_file, "wb")
            try:
                wav_writer.setframerate(self._frame_rate)
                wav_writer.setsampwidth(self._sample_width)
                wav_writer.setnchannels(self._channels)
                wav_writer.writeframes(b''.join(data))
                wave_data = wav_file.getvalue()
            finally:
                wav_writer.close()

        y, _ = librosa.core.load(wave_data, sr=self._frame_rate, offset=0.5)
        return y
