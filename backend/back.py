# back.py
import os
# from celery import Celery
import torch
import json
from yt_dlp import YoutubeDL
import whisper
from pyannote.audio import Pipeline as PyAnnotePipeline
from dotenv import load_dotenv
import math # Import math for timestamp formatting
# Celery configuration
# app = Celery('yt_transcriber', broker='redis://localhost:6379/0')

load_dotenv()
if os.getenv("HUGGINGFACE_TOKEN") is None:
    raise ValueError("HUGGINGFACE_TOKEN is not set")

# --- Timestamp Formatting Helper ---
def format_timestamp(seconds: float) -> str:
    """Formats seconds into HH:MM:SS.ms string."""
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000

    minutes = milliseconds // 60_000
    milliseconds %= 60_000

    seconds_int = milliseconds // 1_000
    milliseconds %= 1_000

    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d}.{milliseconds:03d}"

# --- End Helper ---

# Download audio from YouTube
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        print(f"⏬ Downloading: {percent} | Speed: {speed} | ETA: {eta}", end='\r')
    elif d['status'] == 'finished':
        print(f"\n✅ Download complete: {d['filename']}")

def download_audio(youtube_url, output_dir='downloads'):
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            # 'preferredquality': '192',
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=True)
        return os.path.join(output_dir, f"{info_dict['id']}.wav")


def find_speaker_for_segment(start, end, diarization_result):
    for turn, _, speaker in diarization_result.itertracks(yield_label=True):
        if turn.start <= start and end <= turn.end:
            return speaker
    return "UNKNOWN"


# Celery task for transcription
# @app.task
def transcribe_youtube_audio(youtube_url):
    audio_path = download_audio(youtube_url)

    # Transcription (Whisper)
    whisper_model = whisper.load_model("base")
    result = whisper_model.transcribe(audio_path)
    
    # Save Whisper transcription result
    
    whisper_output_path = audio_path.replace('.wav', '_whisper_transcription.json')
    with open(whisper_output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # print("done with whisper")

    # audio_path = "downloads/-ftgC4oWf6s.wav"
    # whisper_output_path = "downloads/-ftgC4oWf6s_whisper_transcription.json"

    # Load the saved Whisper transcription
    with open(whisper_output_path, 'r', encoding='utf-8') as f:
        result = json.load(f)
    print("Loaded Whisper transcription from file")

    # --- GPU/MPS Check ---
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        device = torch.device("mps")
        print("Using MPS (Apple Silicon GPU)")
    else:
        device = torch.device("cpu")
        print("MPS not available, using CPU")
    # --- End GPU/MPS Check ---

    # Diarization (PyAnnote)
    # Load the pipeline first (usually loads to CPU by default)
    diarization_pipeline = PyAnnotePipeline.from_pretrained(
        "pyannote/speaker-diarization", use_auth_token= os.getenv("HUGGINGFACE_TOKEN")
    )
    # Move the pipeline to the selected device
    diarization_pipeline.to(device)
    print(f"Diarization pipeline loaded to {device}")

    diarization_result = diarization_pipeline(audio_path)

    print("done with diarization")

    # Combine transcription + speaker + timestamps
    speaker_output_lines = []
    for segment in result['segments']:
        start = segment['start']
        end = segment['end']
        text = segment['text'].strip()
        
        # Get speaker
        speaker = find_speaker_for_segment(start, end, diarization_result)
        
        # Format timestamps
        formatted_start = format_timestamp(start)
        formatted_end = format_timestamp(end)
        
        # Create the output line with timestamps
        line = f"[{formatted_start} --> {formatted_end}] [{speaker}] {text}"
        speaker_output_lines.append(line)

    print("done with speaker output lines")
    text_output_path = audio_path.replace('.wav', '_with_speakers.txt')
    with open(text_output_path, 'w') as f:
        f.write("\n".join(speaker_output_lines))

    return text_output_path

if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/watch?v=" + "whatever you want"

    transcribe_youtube_audio(youtube_url)
