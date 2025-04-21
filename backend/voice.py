import sounddevice as sd
from scipy.io.wavfile import write

def record_audio(filename='output.wav', duration=10, samplerate=44100):
    print(f"🎙️ Recording for {duration} seconds... Speak now.")
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    write(filename, samplerate, audio_data)
    print(f"✅ Saved recording to {filename}")

# Example usage
record_audio(filename='my_voice.wav', duration=5)  # 5 seconds
