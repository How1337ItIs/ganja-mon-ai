#!/usr/bin/env python3
"""List all sources and their properties"""

from obswebsocket import obsws, requests as obs_requests
import json

ws = obsws('localhost', 4455, 'h2LDVnmFYDUpSVel')
ws.connect()

print("All Input Sources:\n")

inputs_response = ws.call(obs_requests.GetInputList())
inputs = inputs_response.getInputs()

for inp in inputs:
    name = inp.get('inputName', 'Unknown')
    kind = inp.get('inputKind', 'Unknown')

    # Get source settings
    try:
        settings_response = ws.call(obs_requests.GetInputSettings(inputName=name))
        settings = settings_response.getInputSettings()

        print(f"Source: {name}")
        print(f"  Type: {kind}")

        # Try to get dimensions if available
        if 'width' in settings:
            print(f"  Size: {settings.get('width')}x{settings.get('height')}")

        print()
    except Exception as e:
        print(f"Source: {name} ({kind}) - Could not get settings")
        print()

ws.disconnect()
