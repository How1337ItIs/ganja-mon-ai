#!/usr/bin/env python3
"""Search ElevenLabs for Jamaican voices"""
import requests
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('ELEVENLABS_API_KEY')
headers = {'xi-api-key': api_key}

# Search shared voices for jamaican
url = 'https://api.elevenlabs.io/v1/shared-voices?page_size=20&search=jamaican'
r = requests.get(url, headers=headers)
data = r.json()

print('=== SHARED JAMAICAN VOICES ===')
for v in data.get('voices', [])[:15]:
    name = v.get('name', 'N/A')
    vid = v.get('voice_id', 'N/A')
    accent = v.get('accent', 'N/A')
    desc = v.get('description', '')[:80]
    print(f'Name: {name}')
    print(f'ID: {vid}')
    print(f'Accent: {accent}')
    print(f'Desc: {desc}')
    print('---')

# Also search for rasta/reggae
print('\n=== RASTA/REGGAE VOICES ===')
url2 = 'https://api.elevenlabs.io/v1/shared-voices?page_size=20&search=rasta'
r2 = requests.get(url2, headers=headers)
data2 = r2.json()
for v in data2.get('voices', [])[:10]:
    name = v.get('name', 'N/A')
    vid = v.get('voice_id', 'N/A')
    accent = v.get('accent', 'N/A')
    print(f'{name} | {vid} | {accent}')
