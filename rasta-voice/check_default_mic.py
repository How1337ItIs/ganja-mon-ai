import sounddevice as sd
devs = sd.query_devices()

# Get default input
default_in = sd.default.device[0]
print(f"\n*** DEFAULT INPUT: Device {default_in} - {devs[default_in]['name']} ***\n")

print("=== ALL INPUT DEVICES ===\n")
for i, d in enumerate(devs):
    if d['max_input_channels'] > 0:
        marker = " <-- DEFAULT" if i == default_in else ""
        print(f"  [{i:2}] {d['name'][:45]:<45} ({d['max_input_channels']} ch){marker}")
