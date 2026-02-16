from youtube_transcript_api import YouTubeTranscriptApi

video_id = 'BwfzlPIvGeU'

try:
    # Try the newer API syntax
    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id)
    
    # Format and save the transcript
    full_text = []
    for entry in transcript:
        timestamp = entry.start
        text = entry.text
        full_text.append(f"[{timestamp:.1f}s] {text}")
    
    transcript_content = '\n'.join(full_text)
    
    # Save to file
    with open('hydroponic_diy_transcript.txt', 'w', encoding='utf-8') as f:
        f.write(f"# YouTube Video Transcript\n")
        f.write(f"# Video: World's Most Simple $5 DIY Hydroponic Setup QUICK EZ & CHEAP\n")
        f.write(f"# URL: https://www.youtube.com/watch?v={video_id}\n")
        f.write(f"# ---\n\n")
        f.write(transcript_content)
    
    print("Transcript saved to hydroponic_diy_transcript.txt")
    print(f"\nTotal entries: {len(transcript)}")
    print("\n--- FULL TRANSCRIPT ---\n")
    print(transcript_content)
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
