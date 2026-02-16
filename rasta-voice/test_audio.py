import sounddevice as sd
print("Querying audio devices...")
try:
    devices = sd.query_devices()
    print(f"\nFound {len(devices)} devices:")
    for i, dev in enumerate(devices):
        print(f"  {i}: {dev['name']}")
    print("\nDone!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
