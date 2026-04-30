import json
import os
import sys
import wave
import zipfile
import urllib.request
from pathlib import Path

_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
_FRAME_RATE = 16000


def _model_dir() -> Path:
    from plugins.speech2text.settings import stt_model_path
    return stt_model_path()


def ensure_model() -> Path:
    p = _model_dir()
    if p.exists() and any(p.iterdir()):
        return p
    vosk_dir = p.parent
    vosk_dir.mkdir(parents=True, exist_ok=True)
    zip_path = vosk_dir / "vosk-model-small-ru.zip"
    urllib.request.urlretrieve(_MODEL_URL, str(zip_path))
    with zipfile.ZipFile(str(zip_path), 'r') as zf:
        top = {n.split('/')[0] for n in zf.namelist()}
        prefix = top.pop() + '/'
        for info in zf.infolist():
            if info.filename.startswith(prefix):
                info.filename = info.filename[len(prefix):]
                if info.filename:
                    zf.extract(info, str(p))
    zip_path.unlink(missing_ok=True)
    return p


def transcribe(wav_path: str) -> str:
    from plugins.speech2text.vosk_shim import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(0)

    model_dir = ensure_model()
    model = Model(str(model_dir))

    wf = wave.open(wav_path, "rb")
    rate = wf.getframerate()
    channels = wf.getnchannels()
    sample_width = wf.getsampwidth()

    raw = wf.readframes(wf.getnframes())
    wf.close()

    if rate != _FRAME_RATE or channels != 1:
        import audioop
        if channels > 1:
            raw = audioop.tomono(raw, sample_width, 1, 0)
        if rate != _FRAME_RATE:
            raw, _ = audioop.ratecv(raw, sample_width, 1, rate, _FRAME_RATE, None)
        rate = _FRAME_RATE

    rec = KaldiRecognizer(model, rate)
    rec.SetWords(True)

    chunk_size = 4000
    offset = 0
    while offset < len(raw):
        chunk = raw[offset:offset + chunk_size]
        if not chunk:
            break
        rec.AcceptWaveform(chunk)
        offset += chunk_size

    result = json.loads(rec.FinalResult())
    text = result.get("text", "")

    try:
        text = _restore_punctuation(text)
    except Exception:
        pass

    return text


def _restore_punctuation(text: str) -> str:
    import torch
    checkpoint_dir = Path(__file__).resolve().parent / "recasepunc"
    checkpoint = checkpoint_dir / "checkpoint"
    if not checkpoint.exists():
        return text

    import subprocess
    result = subprocess.run(
        [sys.executable, str(checkpoint_dir / "recasepunc.py"), "predict", str(checkpoint)],
        input=text, capture_output=True, text=True, timeout=30,
    )
    return result.stdout.strip() if result.stdout.strip() else text
