import sounddevice as sd
devs = sd.query_devices()
print("\n=== OUTPUT DEVICES ===\n")
for i, d in enumerate(devs):
    if d['max_output_channels'] > 0:
        print(f"  [{i:2}] {d['name'][:50]:<50} ({d['max_output_channels']} ch, {int(d['default_samplerate'])}Hz)")
