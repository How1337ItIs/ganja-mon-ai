#!/usr/bin/env python3
"""
LIVE Rasta Voice Pipeline with RVC - Twitter Spaces Ready

Mic -> Deepgram STT -> Groq LLM (Patois) -> edge-tts -> RVC (Jamaican) -> VB-Cable -> Twitter

Uses Mr.Bomboclaut RVC model for authentic Jamaican voice.
GPU accelerated with PyTorch 2.9.1+cu128 (RTX 5070 Ti sm_120 supported).
"""

import os
import sys
import asyncio
import time
import json
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv

import numpy as np
import sounddevice as sd
import aiohttp
from groq import Groq

# Suppress PyTorch CUDA warnings for unsupported GPU
import warnings
warnings.filterwarnings("ignore", message=".*CUDA capability sm_120.*")

# Fix PyTorch 2.6+ weights_only default change that breaks fairseq
import torch
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

load_dotenv(Path(__file__).parent / ".env")

# =============================================================================
# Configuration
# =============================================================================

DEEPGRAM_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# RVC Model paths
RVC_MODEL = Path(__file__).parent / "rvc_models" / "Mr.Bomboclaut.pth"
RVC_INDEX = Path(__file__).parent / "rvc_models" / "added_IVF126_Flat_nprobe_1_Mr.Bomboclaut_v2.index"

# edge-tts voice (neutral male for RVC to convert)
EDGE_TTS_VOICE = "en-US-GuyNeural"

SAMPLE_RATE = 16000
TTS_SAMPLE_RATE = 24000  # edge-tts output

# FFmpeg path
FFMPEG_PATH = Path.home() / "Downloads" / "ffmpeg-bin" / "ffmpeg.exe"

# =============================================================================
# Audio Device Selection
# =============================================================================

def find_output_device():
    """Find VB-Cable or fallback to default output device"""
    devices = sd.query_devices()

    for i, d in enumerate(devices):
        if d['max_output_channels'] > 0:
            name_lower = d['name'].lower()
            if 'cable' in name_lower and 'input' in name_lower:
                print(f"[AUDIO] Found VB-Cable: Device {i} - {d['name']}")
                return i

    default_out = sd.default.device[1]
    print(f"[WARN] VB-Cable not found, using default: {devices[default_out]['name']}")
    return default_out

def list_output_devices():
    """List all output devices"""
    print("\n[OUTPUT DEVICES]")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_output_channels'] > 0:
            marker = " <-- VB-CABLE" if 'cable' in d['name'].lower() else ""
            default = " [DEFAULT]" if i == sd.default.device[1] else ""
            print(f"  {i}: {d['name']}{default}{marker}")

# =============================================================================
# Irie Rasta Prompt
# =============================================================================

IRIE_PROMPT = """TRANSLATE to Jamaican Patois. ONLY translate - don't add extra content.

RULES:
- Just convert the words to patois, don't expand or explain
- "I/me" → "mi", "we" → "wi", "you" → "yuh", "them" → "dem"
- "the" → "di", "this" → "dis", "that" → "dat"
- "going" → "gwaan", "what" → "wah", "don't" → "nah"
- Can add "mon", "bredren", "ya know" naturally
- Use "eye-ree" for "irie" (phonetic spelling)
- "MON" when mentioned = token AND "mon" (man) - play with it

EMOTIONS (use sparingly):
- [laughs] for excitement
- [chuckles] for amusement

EXAMPLES:
- "Hello" → "Wah gwaan!"
- "Alright" → "Seen, mon."
- "What's up everyone" → "Wah gwaan, massive!"
- "Check out the plant" → "Check out di plant, bredren."
- "This is amazing" → "Dis eye-ree fi real!"

CRITICAL: ONLY translate. Do NOT add context about streams or tokens unless I mention them."""

# =============================================================================
# Pipeline
# =============================================================================

class RastaLiveRVC:
    def __init__(self, output_device=None):
        self.groq = Groq(api_key=GROQ_KEY)
        self.rvc = None  # Lazy load

        self.processing = False
        self.running = False
        self.latencies = []
        self.audio_queue = asyncio.Queue()

        self.output_device = output_device if output_device is not None else find_output_device()

    def _init_rvc(self):
        """Initialize RVC (lazy load to speed up startup)"""
        if self.rvc is not None:
            return

        print("[RVC] Loading Mr.Bomboclaut model...")
        from rvc_python.infer import RVCInference

        self.rvc = RVCInference(device="cuda")  # GPU accelerated - RTX 5070 Ti
        self.rvc.load_model(str(RVC_MODEL), index_path=str(RVC_INDEX))
        print("[RVC] Model loaded!")

    def transform(self, text: str) -> str:
        """Transform text to irie patois"""
        # Scale max_tokens based on input length
        word_count = len(text.split())
        if word_count <= 5:
            max_tokens = 25  # Short input = short response
        elif word_count <= 12:
            max_tokens = 40  # Medium input
        else:
            max_tokens = 60  # Longer input

        response = self.groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": IRIE_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.5,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    async def tts_edge(self, text: str, output_path: Path):
        """Generate TTS with edge-tts"""
        import edge_tts
        communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
        await communicate.save(str(output_path))

    def convert_rvc(self, input_path: Path, output_path: Path):
        """Convert voice with RVC"""
        self._init_rvc()
        self.rvc.infer_file(str(input_path), str(output_path))

    def play_audio(self, audio_path: Path):
        """Play audio file via sounddevice to VB-Cable"""
        # Convert to PCM using ffmpeg
        process = subprocess.Popen(
            [
                str(FFMPEG_PATH),
                '-i', str(audio_path),
                '-f', 's16le',
                '-acodec', 'pcm_s16le',
                '-ar', str(TTS_SAMPLE_RATE),
                '-ac', '1',
                'pipe:1'
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        pcm_data, _ = process.communicate()

        samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32)
        samples = samples / 32768.0

        # Add silence padding
        padding = np.zeros(int(TTS_SAMPLE_RATE * 0.3), dtype=np.float32)
        samples = np.concatenate([samples, padding])

        sd.play(samples, samplerate=TTS_SAMPLE_RATE, device=self.output_device)
        sd.wait()

    async def speak(self, text: str):
        """Full TTS + RVC pipeline"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tts_path = Path(tmpdir) / "tts.mp3"
            rvc_path = Path(tmpdir) / "rvc.wav"

            # edge-tts
            await self.tts_edge(text, tts_path)

            # RVC conversion (run in executor to not block)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.convert_rvc, tts_path, rvc_path)

            # Play result
            await loop.run_in_executor(None, self.play_audio, rvc_path)

    async def process_transcript(self, text: str):
        """Full pipeline: transform + speak"""
        if not text.strip() or self.processing:
            return

        self.processing = True
        start = time.perf_counter()

        try:
            print(f"\n[YOU] \"{text}\"")

            # Transform to patois
            rasta = self.transform(text)
            print(f"[RASTA] \"{rasta}\"")

            # Speak with RVC
            await self.speak(rasta)

            total = (time.perf_counter() - start) * 1000
            self.latencies.append(total)
            print(f"[TIME] {total:.0f}ms")

        finally:
            self.processing = False

    async def run(self):
        """Start the live pipeline"""
        print("=" * 60, flush=True)
        print("RASTA LIVE VOICE (RVC) - Twitter Spaces Ready", flush=True)
        print("=" * 60, flush=True)
        print(f"Voice: Mr.Bomboclaut (Jamaican TikTok)", flush=True)
        print(f"Output: Device {self.output_device} - {sd.query_devices(self.output_device)['name']}", flush=True)
        print("Speak into your mic. Your voice will be transformed.", flush=True)
        print("Press Ctrl+C to stop.", flush=True)
        print(flush=True)

        # Pre-load RVC model
        print("[INIT] Pre-loading RVC model...", flush=True)
        self._init_rvc()

        # Deepgram websocket URL
        url = f"wss://api.deepgram.com/v1/listen?model=nova-2&language=en&smart_format=true&punctuate=true&encoding=linear16&sample_rate={SAMPLE_RATE}&channels=1&interim_results=false&endpointing=300"

        self.running = True

        def mic_callback(indata, frames, time_info, status):
            if self.running:
                audio_int16 = (indata * 32767).astype(np.int16)
                try:
                    self.audio_queue.put_nowait(audio_int16.tobytes())
                except:
                    pass

        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    url,
                    headers={"Authorization": f"token {DEEPGRAM_KEY}"}
                ) as ws:
                    print("[OK] Connected to Deepgram", flush=True)
                    print("[MIC] Microphone active - speak now!\n", flush=True)

                    async def send_audio():
                        while self.running:
                            try:
                                audio = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
                                await ws.send_bytes(audio)
                            except asyncio.TimeoutError:
                                pass
                            except Exception as e:
                                if self.running:
                                    print(f"Send error: {e}")
                                break

                    async def receive_transcripts():
                        while self.running:
                            try:
                                msg = await asyncio.wait_for(ws.receive(), timeout=0.5)
                                if msg.type == aiohttp.WSMsgType.TEXT:
                                    data = json.loads(msg.data)
                                    if data.get("type") == "Results":
                                        transcript = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                                        is_final = data.get("is_final", False)
                                        if transcript and is_final:
                                            await self.process_transcript(transcript)
                                elif msg.type == aiohttp.WSMsgType.CLOSED:
                                    break
                                elif msg.type == aiohttp.WSMsgType.ERROR:
                                    print(f"WS error: {ws.exception()}")
                                    break
                            except asyncio.TimeoutError:
                                pass
                            except Exception as e:
                                if self.running:
                                    print(f"Receive error: {e}")

                    with sd.InputStream(
                        samplerate=SAMPLE_RATE,
                        channels=1,
                        dtype=np.float32,
                        blocksize=1024,
                        callback=mic_callback
                    ):
                        await asyncio.gather(
                            send_audio(),
                            receive_transcripts()
                        )

        except KeyboardInterrupt:
            print("\n\n[STOP] Stopping...")
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        self.running = False

        if self.latencies:
            avg = sum(self.latencies) / len(self.latencies)
            print(f"\n[STATS] Average latency: {avg:.0f}ms")

        print("[DONE] One love, bredren!")


# =============================================================================
# Entry
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rasta Voice Pipeline with RVC")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    parser.add_argument("--output-device", type=int, help="Output device ID (default: auto-detect VB-Cable)")
    parser.add_argument("--test", action="store_true", help="Test mode: output to speakers instead of VB-Cable")
    args = parser.parse_args()

    if args.test:
        args.output_device = sd.default.device[1]
        print(f"[TEST MODE] Output to speakers: {sd.query_devices(args.output_device)['name']}")

    if args.list_devices:
        list_output_devices()
        exit(0)

    # Check keys
    missing = []
    if not DEEPGRAM_KEY: missing.append("DEEPGRAM_API_KEY")
    if not GROQ_KEY: missing.append("GROQ_API_KEY")

    if missing:
        print(f"[ERROR] Missing: {', '.join(missing)}")
        print("Add them to rasta-voice/.env")
        exit(1)

    # Check RVC model
    if not RVC_MODEL.exists():
        print(f"[ERROR] RVC model not found: {RVC_MODEL}")
        exit(1)

    pipeline = RastaLiveRVC(output_device=args.output_device)
    asyncio.run(pipeline.run())
