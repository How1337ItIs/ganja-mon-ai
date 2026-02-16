# Megaphone Echo Loop Fix — Codex Handoff

## THE PROBLEM
The Rasta Mon Megaphone (`raspberry-pi/megaphone.py`) has a **feedback loop**: the megaphone plays Rasta voice TTS → the lapel mic (TX1) picks it up → Deepgram transcribes it → Groq translates it AGAIN → infinite loop.

The user speaks CONTINUOUSLY and should never have to stop. The Rasta Mon should keep up, translating each chunk in sequence while the user keeps talking through the next chunk.

## THE SOLUTION: Software Acoustic Echo Cancellation (AEC)

We have a **Hollyland Lark A1** with 2 wireless transmitters feeding stereo into one USB-C receiver:
- **Left channel (TX1)** = user's lapel mic = user voice + megaphone echo  
- **Right channel (TX2)** = clipped to megaphone = megaphone echo (reference signal)

**Use NLMS (Normalized Least Mean Squares) adaptive filter** to subtract the megaphone echo from the user's channel:

```
cleaned_signal = left_channel - nlms_filter(right_channel)
```

Then send `cleaned_signal` as **mono** to Deepgram (`channels=1`, no multichannel needed).

### Implementation in `mic_callback`:

```python
# In __init__:
self._aec_filter_len = 512  # taps (~10ms at 48kHz)
self._aec_weights = np.zeros(self._aec_filter_len)
self._aec_mu = 0.3  # NLMS step size (0.1-0.5, tune as needed)
self._aec_ref_buffer = np.zeros(self._aec_filter_len)

# In mic_callback:
def mic_callback(indata, frames, time_info, status):
    if not (self.running and self.connected):
        return
    
    left = indata[:, 0].copy()   # TX1: user + echo
    right = indata[:, 1].copy()  # TX2: echo reference
    
    # NLMS adaptive echo cancellation
    cleaned = np.zeros_like(left)
    for i in range(len(left)):
        # Shift reference buffer
        self._aec_ref_buffer = np.roll(self._aec_ref_buffer, 1)
        self._aec_ref_buffer[0] = right[i]
        
        # Estimate echo from reference
        echo_estimate = np.dot(self._aec_weights, self._aec_ref_buffer)
        
        # Remove echo
        cleaned[i] = left[i] - echo_estimate
        
        # Update filter weights (NLMS)
        power = np.dot(self._aec_ref_buffer, self._aec_ref_buffer) + 1e-10
        self._aec_weights += (self._aec_mu / power) * cleaned[i] * self._aec_ref_buffer
    
    # Noise gate on cleaned signal
    rms = np.sqrt(np.mean(cleaned ** 2))
    if rms < self.NOISE_GATE_RMS:
        return
    
    # Send cleaned mono to Deepgram
    audio_int16 = (cleaned * 32767).astype(np.int16)
    try:
        audio_queue.put_nowait(audio_int16.tobytes())
    except asyncio.QueueFull:
        pass
```

### CRITICAL: Revert Deepgram to mono
Change the Deepgram URL back to `channels=1` (no multichannel) since we're now sending cleaned mono audio.

### Performance Note  
The per-sample NLMS loop in Python will be SLOW on Pi Zero 2 W. **Vectorize it**: process the entire block at once using `scipy.signal.lfilter` or a block-based NLMS. Alternatively, use a simpler approach:

**Simple block subtraction (faster, less accurate but may be good enough):**
```python
# Estimate alpha = correlation coefficient between channels
alpha = np.dot(left, right) / (np.dot(right, right) + 1e-10)
alpha = np.clip(alpha, 0, 2.0)  # safety bound
cleaned = left - alpha * right
```

This is ONE line of numpy — runs instantly. Try this first. If the echo cancellation quality is insufficient, upgrade to block NLMS.

## WHAT TO CHANGE IN megaphone.py

1. **`__init__`**: Add AEC state variables
2. **`mic_callback`**: Record stereo, apply AEC, send cleaned mono
3. **Deepgram URL**: Back to `channels=1`, remove `multichannel=true`, keep `diarize=true`
4. **`receive_transcripts`**: Remove the `channel_index` filtering (back to simple mono processing)
5. **Keep**: noise gate, echo word detection (as tertiary defense), KeepAlive

## DEPLOY & TEST
```bash
# Deploy
powershell.exe -Command "Get-Content 'raspberry-pi\megaphone.py' -Raw | ssh midaswhale@192.168.125.222 'cat > /home/midaswhale/megaphone/megaphone.py'"

# Run  
ssh midaswhale@192.168.125.222 'cd /home/midaswhale/megaphone && source venv/bin/activate && python3 megaphone.py --no-gpio --input-device 0'
```
Password: `newpass1337**`

## CURRENT FILE STATE
- Recording: stereo `channels=2` from Lark A1 USB
- Deepgram: `multichannel=true` with `channels=2` (CHANGE to mono)
- Noise gate: 0.002 RMS
- Echo word detection: 40% overlap threshold, 15s window
- KeepAlive: every 8s
- Transcript filtering: by `channel_index[0]` (REMOVE, use AEC instead)
