#!/usr/bin/env python3
"""
Rasta Mon Megaphone - Raspberry Pi Version

Simplified version for hardware megaphone device:
- Single audio output (speaker/megaphone)
- No dual-output routing
- GPIO controls for power/status
- Optimized for low latency (conversation mode)
"""

import os
import sys
import json
import asyncio
import time
import signal
import argparse
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from collections import deque
from datetime import datetime

import numpy as np
import sounddevice as sd
from scipy import signal as scipy_signal
from dotenv import load_dotenv
from websockets import connect as ws_connect
from websockets.exceptions import ConnectionClosed, WebSocketException
from openai import OpenAI
from elevenlabs import ElevenLabs

# Try to import RPi.GPIO (only available on Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("Warning: RPi.GPIO not available (not running on Raspberry Pi)")

# Load environment
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import shared components from main pipeline
# (In a real implementation, you'd import from rasta_live.py)
# For now, we'll include the essential parts

VOICE_CONFIG_FILE = Path(__file__).parent / "voice_config.json"

def _clamp01(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0

def load_voice_config() -> dict:
    """Load voice configuration from JSON file."""
    cfg = {"stability": 0.0, "style": 1.0, "temperature": 0.7}
    try:
        if VOICE_CONFIG_FILE.exists():
            data = json.loads(VOICE_CONFIG_FILE.read_text(encoding="utf-8"))
            cfg["stability"] = _clamp01(data.get("stability", cfg["stability"]))
            cfg["style"] = _clamp01(data.get("style", cfg["style"]))
            cfg["temperature"] = _clamp01(data.get("temperature", cfg["temperature"]))
    except Exception:
        pass
    return cfg

# Import the system prompt from main file (or copy it here)
# For brevity, assuming it's imported or defined elsewhere
# You'd copy the RASTA_SYSTEM_PROMPT from rasta_live.py

@dataclass
class Config:
    deepgram_key: str = os.getenv("DEEPGRAM_API_KEY", "")
    groq_key: str = os.getenv("GROQ_API_KEY", "")
    elevenlabs_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")
    
    sample_rate: int = 48000
    output_sample_rate: int = 24000
    chunk_size: int = 1024
    
    # Simplified: just input and output devices
    input_device: Optional[int] = None  # USB mic
    output_device: Optional[int] = None  # Speaker/megaphone (default if None)
    
    # Always use conversation mode for megaphone (lower latency)
    mode: str = "conversation"

config = Config()

# GPIO Configuration (Raspberry Pi only)
GPIO_POWER_BUTTON = 3  # Physical pin 5
GPIO_STATUS_LED = 18   # Physical pin 12
GPIO_BATTERY_LOW = 24  # Physical pin 18 (optional)

def setup_gpio():
    """Initialize GPIO pins for hardware controls."""
    if not HAS_GPIO:
        logger.warning("GPIO not available - hardware controls disabled")
        return
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_POWER_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(GPIO_STATUS_LED, GPIO.OUT)
        GPIO.setup(GPIO_BATTERY_LOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Set LED to indicate ready
        GPIO.output(GPIO_STATUS_LED, GPIO.HIGH)
        logger.info("GPIO initialized")
    except Exception as e:
        logger.error(f"GPIO setup failed: {e}")

def cleanup_gpio():
    """Clean up GPIO on exit."""
    if HAS_GPIO:
        try:
            GPIO.cleanup()
        except:
            pass

def check_battery_low() -> bool:
    """Check if battery is low (GPIO pin low = battery low)."""
    if not HAS_GPIO:
        return False
    
    try:
        return GPIO.input(GPIO_BATTERY_LOW) == GPIO.LOW
    except:
        return False

def set_status_led(state: bool):
    """Set status LED on/off."""
    if not HAS_GPIO:
        return
    
    try:
        GPIO.output(GPIO_STATUS_LED, GPIO.HIGH if state else GPIO.LOW)
    except:
        pass

# Simplified TTS class (single output only)
class ElevenLabsTTS:
    """Text-to-speech using ElevenLabs - single output device."""
    
    ELEVENLABS_SAMPLE_RATE = 24000
    OUTPUT_SAMPLE_RATE = 48000
    
    def __init__(self, api_key: str, voice_id: str, output_device: Optional[int] = None):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = "eleven_v3"
        self.output_device = output_device
    
    def _resample(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio using scipy."""
        if from_rate == to_rate:
            return audio
        new_length = int(len(audio) * to_rate / from_rate)
        return scipy_signal.resample(audio, new_length).astype(np.float32)
    
    def speak(self, text: str) -> float:
        """Generate and play speech to single output device."""
        start = time.perf_counter()
        
        try:
            vc = load_voice_config()
            audio_data = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="pcm_24000",
                voice_settings={
                    "stability": float(vc.get("stability", 0.0)),
                    "similarity_boost": 0.5,
                    "style": float(vc.get("style", 1.0)),
                    "use_speaker_boost": True
                }
            )
            
            # Collect all chunks
            all_chunks = b"".join(audio_data)
            audio_24k = np.frombuffer(all_chunks, dtype=np.int16).astype(np.float32) / 32768.0
            audio_48k = self._resample(audio_24k, self.ELEVENLABS_SAMPLE_RATE, self.OUTPUT_SAMPLE_RATE)
            
            # Play to single output device (simplified - no threading needed)
            sd.play(audio_48k, samplerate=self.OUTPUT_SAMPLE_RATE, device=self.output_device)
            sd.wait()  # Wait for playback to complete
            
            latency = (time.perf_counter() - start) * 1000
            return latency
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return 0

# Import or copy the RastaDialectTransformer and SmartBatcher classes
# For brevity, assuming they're imported from rasta_live.py or copied here
# You'd copy the classes from the main file

# Simplified pipeline (single output)
class RastaMegaphonePipeline:
    """Simplified pipeline for megaphone hardware."""
    
    def __init__(self):
        # Import transformer and batcher from main file or copy here
        # For now, placeholder - you'd use the actual classes
        from rasta_live import RastaDialectTransformer, SmartBatcher, ConversationBuffer
        
        self.transformer = RastaDialectTransformer(config.groq_key)
        self.tts = ElevenLabsTTS(
            config.elevenlabs_key,
            config.elevenlabs_voice_id,
            output_device=config.output_device
        )
        self.batcher = SmartBatcher(mode=config.mode)
        self.conversation = ConversationBuffer(max_exchanges=10)
        
        self.running = False
        self.connected = False
        self.websocket = None
        self._mic_stream = None
    
    async def process_batch(self, combined_text: str):
        """Process batched transcript."""
        if not combined_text.strip():
            return
        
        logger.info(f"🎤 Input: \"{combined_text}\"")
        
        # Transform with LLM
        context = self.conversation.format_for_prompt(n=5)
        rasta_text, llm_latency = await self.transformer.transform(combined_text, context)
        
        # Filter meta-commentary
        if rasta_text.startswith('(') or 'Note:' in rasta_text:
            logger.warning(f"Filtered: \"{rasta_text}\"")
            return
        
        logger.info(f"🎙️ Rasta: \"{rasta_text}\" ({llm_latency:.0f}ms)")
        
        # Generate and play TTS
        tts_latency = await asyncio.to_thread(self.tts.speak, rasta_text)
        
        # Log transcript
        transcript_log = Path(__file__).parent / "megaphone_transcripts.jsonl"
        with open(transcript_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "original": combined_text,
                "patois": rasta_text
            }) + '\n')
        
        logger.info(f"✅ Complete: LLM={llm_latency:.0f}ms, TTS={tts_latency:.0f}ms")
    
    async def _run_connection(self):
        """Run WebSocket connection to Deepgram."""
        deepgram_url = (
            f"wss://api.deepgram.com/v1/listen?"
            f"encoding=linear16&sample_rate={config.sample_rate}&channels=1"
            f"&model=nova-2&punctuate=true&interim_results=true"
            f"&endpointing=500&smart_format=true"
        )
        
        headers = {"Authorization": f"Token {config.deepgram_key}"}
        
        try:
            async with ws_connect(
                deepgram_url,
                additional_headers=headers,
                ping_interval=15,
                ping_timeout=10,
                close_timeout=5
            ) as ws:
                self.websocket = ws
                self.connected = True
                set_status_led(True)  # LED on = connected
                logger.info("Connected to Deepgram")
                
                # Start microphone
                audio_queue = asyncio.Queue()
                
                def mic_callback(indata, frames, time_info, status):
                    if self.running and self.connected:
                        audio_int16 = (indata * 32767).astype(np.int16)
                        try:
                            audio_queue.put_nowait(audio_int16.tobytes())
                        except asyncio.QueueFull:
                            pass
                
                self._mic_stream = sd.InputStream(
                    samplerate=config.sample_rate,
                    channels=1,
                    dtype=np.float32,
                    blocksize=config.chunk_size,
                    callback=mic_callback,
                    device=config.input_device
                )
                self._mic_stream.start()
                logger.info("Microphone active - speak into megaphone!")
                
                # Send audio
                async def send_audio():
                    while self.running and self.connected:
                        try:
                            audio = await asyncio.wait_for(audio_queue.get(), timeout=1.0)
                            await ws.send(audio)
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                            self.connected = False
                            break
                
                # Receive transcripts
                async def receive_transcripts():
                    while self.running and self.connected:
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)
                            
                            if data.get("type") == "Results":
                                alt = data.get("channel", {}).get("alternatives", [{}])[0]
                                transcript = alt.get("transcript", "")
                                is_final = data.get("is_final", False)
                                
                                if transcript and is_final:
                                    self.batcher.add(transcript)
                                    
                                    # Check if batch should be processed
                                    if self.batcher.should_flush():
                                        combined_text, _ = self.batcher.flush()
                                        if combined_text:
                                            await self.process_batch(combined_text)
                                            
                                            # Check battery
                                            if check_battery_low():
                                                logger.warning("Battery low - shutting down in 30 seconds")
                                                await asyncio.sleep(30)
                                                self.running = False
                        
                        except ConnectionClosed:
                            logger.warning("WebSocket closed")
                            self.connected = False
                            break
                        except Exception as e:
                            logger.error(f"Receive error: {e}")
                            self.connected = False
                            break
                
                # Run both tasks
                await asyncio.gather(
                    asyncio.create_task(send_audio()),
                    asyncio.create_task(receive_transcripts()),
                    return_exceptions=True
                )
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            self.connected = False
            set_status_led(False)  # LED off = disconnected
            if self._mic_stream:
                self._mic_stream.stop()
                self._mic_stream.close()
                self._mic_stream = None
    
    async def run(self):
        """Run the megaphone pipeline."""
        logger.info("=" * 60)
        logger.info("RASTA MON MEGAPHONE")
        logger.info("=" * 60)
        logger.info("Speak naturally. Press Ctrl+C to stop.")
        
        self.running = True
        
        try:
            while self.running:
                await self._run_connection()
                if not self.running:
                    break
                logger.info("Reconnecting in 2 seconds...")
                await asyncio.sleep(2)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.running = False
            cleanup_gpio()
            logger.info("Megaphone stopped")

def shutdown_handler(channel):
    """Handle power button press (shutdown after 3 second hold)."""
    logger.info("Power button pressed - shutting down in 3 seconds...")
    time.sleep(3)
    if GPIO.input(GPIO_POWER_BUTTON) == GPIO.LOW:  # Still held
        logger.info("Shutting down...")
        os.system("sudo shutdown -h now")

def main():
    parser = argparse.ArgumentParser(description="Rasta Mon Megaphone")
    parser.add_argument("--input-device", type=int, help="Input device index (USB mic)")
    parser.add_argument("--output-device", type=int, help="Output device index (speaker)")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices")
    args = parser.parse_args()
    
    if args.list_devices:
        devices = sd.query_devices()
        print("\n=== AUDIO DEVICES ===\n")
        print("OUTPUT DEVICES:")
        for i, d in enumerate(devices):
            if d['max_output_channels'] > 0:
                print(f"  {i}: {d['name']}")
        print("\nINPUT DEVICES:")
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"  {i}: {d['name']}")
        return
    
    # Validate API keys
    missing = []
    if not config.deepgram_key:
        missing.append("DEEPGRAM_API_KEY")
    if not config.groq_key:
        missing.append("GROQ_API_KEY")
    if not config.elevenlabs_key:
        missing.append("ELEVENLABS_API_KEY")
    
    if missing:
        logger.error("Missing environment variables:")
        for var in missing:
            logger.error(f"  - {var}")
        sys.exit(1)
    
    # Configure devices
    if args.input_device is not None:
        config.input_device = args.input_device
    if args.output_device is not None:
        config.output_device = args.output_device
    
    # Setup GPIO
    setup_gpio()
    
    # Setup power button handler
    if HAS_GPIO:
        GPIO.add_event_detect(GPIO_POWER_BUTTON, GPIO.FALLING, 
                             callback=shutdown_handler, bouncetime=200)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        cleanup_gpio()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run pipeline
    try:
        pipeline = RastaMegaphonePipeline()
        asyncio.run(pipeline.run())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        cleanup_gpio()
        sys.exit(1)

if __name__ == "__main__":
    main()
