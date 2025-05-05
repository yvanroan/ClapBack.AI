
import os
from datetime import datetime
import torch
import json
from yt_dlp import YoutubeDL
import whisper
from pyannote.audio import Pipeline as PyAnnotePipeline
from dotenv import load_dotenv
import math 


load_dotenv()
if os.getenv("HUGGINGFACE_TOKEN") is None:
    raise ValueError("HUGGINGFACE_TOKEN is not set")


current_dir = os.path.dirname(os.path.abspath(__file__))
grand_parent_dir = os.path.dirname(os.path.abspath(current_dir))
backend_dir = os.path.dirname(os.path.abspath(grand_parent_dir))
data_dir = os.path.join(backend_dir, "data") 
LOG_PATH = os.path.join(data_dir, 'log_transcript.json')


# --- helper ---
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

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        print(f"⏬ Downloading: {percent} | Speed: {speed} | ETA: {eta}")
    elif d['status'] == 'finished':
        print(f"\n✅ Download complete: {d['filename']}")

# --- End Helper ---

def download_audio(url, parent_dir=data_dir):
    audio_folder = os.path.join(parent_dir, 'audio')
    os.makedirs(audio_folder, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{audio_folder}/%(id)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            # 'preferredquality': '192',
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        return os.path.join(audio_folder, f"{info_dict['id']}.wav")

def find_speaker_for_segment(start, end, diarization_result):
    for turn, _, speaker in diarization_result.itertracks(yield_label=True):
        if turn.start <= start and end <= turn.end:
            return speaker
    return "UNKNOWN"

def transcribe_youtube_audio(url, parent_dir = data_dir):
    audio_path = download_audio(url)
    audio_name = audio_path.split("/")[-1]

    whisper_model = whisper.load_model("base")
    result = whisper_model.transcribe(audio_path)

    whisper_transcript_folder = os.path.join(parent_dir, 'whisper_transcript')
    os.makedirs(whisper_transcript_folder, exist_ok=True)

    whisper_output_name = audio_name.replace('.wav', '.json')

    whisper_output_path = os.path.join(whisper_transcript_folder, whisper_output_name)

    with open(whisper_output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # with open(whisper_output_path, 'r', encoding='utf-8') as f:
    #     result = json.load(f)
    # print("Loaded Whisper transcription from file")

    # --- GPU/MPS Check ---
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        device = torch.device("mps")
        print("Using MPS (Apple Silicon GPU)")
    else:
        device = torch.device("cpu")
        print("MPS not available, using CPU")
    # --- End GPU/MPS Check ---

    # Diarization (PyAnnote)
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

    speaker_transcript_folder = os.path.join(parent_dir, 'speaker_transcript')
    os.makedirs(whisper_transcript_folder, exist_ok=True)

    speaker_output_name = audio_name.replace('.wav', '.txt')

    speaker_output_path = os.path.join(speaker_transcript_folder, speaker_output_name)


    with open(speaker_output_path, 'w') as f:
        f.write("\n".join(speaker_output_lines))

    return speaker_output_path

#be very careful with this one
def log_url_from_file(input_file):
    """
    This will be used to keep track of status and number of retries done for multiple link
    """

    with open(input_file, 'r') as f:
        links = [line.strip() for line in f if line.strip().startswith('https://')]

    for link in links:
        log_url(link)

def log_url(url, log_path=LOG_PATH):
    """
    This will be used to keep track of status and number of retries done per link
    """

    # Load or initialize log
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            logs = json.load(f)
    else:
        logs = {}

    print(f"\Logging: {url}")

    retries =0
    
    if url in logs.keys():
        if logs[url]["status"]=="transcribed":
            print(f"Transcription was already achieved for {url}")
            return logs[url]["output_path"]

        retries = logs[url]["retries"]+1

    log_entry= {
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "error": None,
        "retries": retries
    }

    is_final = True

    try:
        final_path = transcribe_youtube_audio(url)
        log_entry["status"] = "transcribed"
        log_entry["output_path"] = final_path
        print(f"✅ {url} was transcribed successfully")

    except Exception as e:
        log_entry["status"] = "failed"
        log_entry["error"] = str(e)
        is_final = False
        print(f"❌ Transcription failed for {url}: {e}") 

    # Update and save log after each url
    logs[url] = log_entry
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)

    return final_path if is_final else None
