#!/usr/bin/env python3
"""
VB-Cable Audio Test
Tests that audio is properly routed through VB-Cable to Twitter Spaces.
"""
import numpy as np
import sounddevice as sd
import time

def list_devices():
    """List all audio devices."""
    devices = sd.query_devices()
    print("\n=== AUDIO DEVICES ===\n")
    for i, d in enumerate(devices):
        io_type = []
        if d['max_input_channels'] > 0:
            io_type.append("IN")
        if d['max_output_channels'] > 0:
            io_type.append("OUT")

        marker = ""
        name_lower = d['name'].lower()
        if "cable input" in name_lower:
            marker = " <-- OUTPUT here (VB-Cable receives audio)"
        elif "cable output" in name_lower:
            marker = " <-- Twitter uses this as 'microphone'"
        elif "headphone" in name_lower:
            marker = " <-- Your headphones"

        print(f"  {i:2d}: [{'/'.join(io_type):>7}] {d['name']}{marker}")
        print(f"       Default SR: {d['default_samplerate']:.0f} Hz")


def test_tone(device_id: int, duration: float = 3.0, frequency: float = 440.0, sample_rate: int = 44100):
    """Play a test tone to a specific device."""
    print(f"\nPlaying {frequency}Hz tone to device {device_id} for {duration}s at {sample_rate}Hz...")

    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)

    # Add a quick fade in/out to avoid clicks
    fade_samples = int(0.01 * sample_rate)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    try:
        sd.play(audio, samplerate=sample_rate, device=device_id, blocking=True)
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")


def test_dual_output(vb_device: int, headphone_device: int, sample_rate: int = 44100):
    """Test playing to both VB-Cable and headphones simultaneously."""
    import threading

    duration = 3.0
    frequency = 440.0

    print(f"\nPlaying tone to BOTH devices:")
    print(f"  VB-Cable: device {vb_device}")
    print(f"  Headphones: device {headphone_device}")
    print(f"  Duration: {duration}s, Frequency: {frequency}Hz, Sample rate: {sample_rate}Hz")

    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)

    # Fade
    fade_samples = int(0.01 * sample_rate)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    def play_to_device(device_id, name):
        try:
            print(f"  Starting playback to {name} (device {device_id})...")
            sd.play(audio, samplerate=sample_rate, device=device_id, blocking=True)
            print(f"  Finished {name}")
        except Exception as e:
            print(f"  Error playing to {name}: {e}")

    threads = []
    t1 = threading.Thread(target=play_to_device, args=(vb_device, "VB-Cable"))
    t2 = threading.Thread(target=play_to_device, args=(headphone_device, "Headphones"))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("Both playbacks complete!")


def find_device(pattern: str) -> int:
    """Find device by name pattern."""
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if pattern.lower() in d['name'].lower():
            return i
    return -1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test VB-Cable audio routing")
    parser.add_argument("--list", action="store_true", help="List all audio devices")
    parser.add_argument("--device", type=int, help="Device index to test")
    parser.add_argument("--vb", action="store_true", help="Test VB-Cable Input")
    parser.add_argument("--headphones", action="store_true", help="Test Headphones")
    parser.add_argument("--dual", action="store_true", help="Test dual output (VB-Cable + Headphones)")
    parser.add_argument("--sr", type=int, default=44100, help="Sample rate (default: 44100)")
    args = parser.parse_args()

    if args.list:
        list_devices()
    elif args.device is not None:
        test_tone(args.device, sample_rate=args.sr)
    elif args.vb:
        vb = find_device("cable input")
        if vb >= 0:
            test_tone(vb, sample_rate=args.sr)
        else:
            print("VB-Cable Input not found!")
    elif args.headphones:
        hp = find_device("headphone")
        if hp >= 0:
            test_tone(hp, sample_rate=args.sr)
        else:
            print("Headphones not found!")
    elif args.dual:
        vb = find_device("cable input")
        hp = find_device("headphone")
        if vb >= 0 and hp >= 0:
            test_dual_output(vb, hp, sample_rate=args.sr)
        else:
            print(f"Devices not found: VB-Cable={vb}, Headphones={hp}")
    else:
        list_devices()
        print("\nUsage:")
        print("  python test_vbcable.py --list          # List devices")
        print("  python test_vbcable.py --device 8      # Test specific device")
        print("  python test_vbcable.py --vb            # Test VB-Cable")
        print("  python test_vbcable.py --headphones    # Test Headphones")
        print("  python test_vbcable.py --dual          # Test both")
        print("  python test_vbcable.py --vb --sr 24000 # Test VB-Cable at 24kHz")
