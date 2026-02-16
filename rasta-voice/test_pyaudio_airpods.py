import pyaudiowpatch as pa
import numpy as np

p = pa.PyAudio()

# Test AirPods device 23
dev_info = p.get_device_info_by_index(23)
print(f"Testing device 23: {dev_info['name']}")
print(f"  Sample rate: {dev_info['defaultSampleRate']}")
print(f"  Channels: {dev_info['maxInputChannels']}")

try:
    stream = p.open(
        format=pa.paInt16,
        channels=1,
        rate=int(dev_info['defaultSampleRate']),
        input=True,
        input_device_index=23,
        frames_per_buffer=1024
    )

    print("\nRecording 2 seconds...")
    frames = []
    for i in range(int(dev_info['defaultSampleRate'] / 1024 * 2)):
        data = stream.read(1024)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    print("SUCCESS! PyAudio can access AirPods!")

except Exception as e:
    print(f"FAILED: {e}")

p.terminate()
