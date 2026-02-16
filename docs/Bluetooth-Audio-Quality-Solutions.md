# Bluetooth Audio Quality — Research & Solutions

Solutions for phasing, dropouts, and choppy Bluetooth audio on **Raspberry Pi Zero 2 W** (e.g. Rasta megaphone → Pi → UGREEN BT509 receiver). Context: shared 2.4 GHz antenna (WiFi + BT), PulseAudio, A2DP.

---

## 1. WiFi/BT coexistence (Pi Zero 2 W firmware)

**Cause:** Built-in WiFi and Bluetooth share one antenna and interfere; BT audio stutters when WiFi is active (e.g. Deepgram/Groq/ElevenLabs).

**Fix A — Update firmware (preferred)**  
Coexistence is in newer Raspberry Pi firmware. On the Pi:

```bash
sudo apt update
sudo apt install firmware-brcm80211
sudo reboot
```

Package version that includes the fix: `firmware-brcm80211=1:20230210-5~bpo11+1+rpt1` or newer. Pi OS Bookworm+ and Moode 8.3.6+ ship it; Trixie may already have it.

**Fix B — Manual coexistence parameters**  
If the package doesn’t fix it, add Broadcom coexistence settings:

1. See which chip variant you have:
   ```bash
   dmesg | grep brcmfmac43436
   ```
   - `BCM43430/1` → config file: `brcmfmac43436s-sdio.txt`
   - `BCM43430/2` → config file: `brcmfmac43436-sdio.txt`

2. Edit the matching file:
   ```bash
   # For BCM43430/1:
   sudo nano /lib/firmware/brcm/brcmfmac43436s-sdio.txt
   # For BCM43430/2:
   sudo nano /lib/firmware/brcm/brcmfmac43436-sdio.txt
   ```

3. Add at the end:
   ```
   # Improved Bluetooth coexistence parameters
   btc_mode=1
   btc_params8=0x4e20
   btc_params1=0x7530
   ```

4. Reboot: `sudo reboot`

**Note:** Improves BT at the cost of some WiFi throughput when BT is active.

**Sources:** [Raspberry Pi Linux #5293](https://github.com/raspberrypi/linux/issues/5293), [Moode Forum](https://moodeaudio.org/forum/showthread.php?tid=5607), [RPi-Distro/firmware-nonfree #33](https://github.com/RPi-Distro/firmware-nonfree/issues/33).

---

## 2. Codec: prefer SBC over LDAC on Pi Zero 2 W

**Cause:** LDAC (especially HQ) uses a lot of 2.4 GHz bandwidth and competes with WiFi; can make dropouts worse.

**Fix:** Force **SBC** for the BT sink (lower bandwidth, more robust with interference). Your pipeline already tried SBC; ensure it’s actually in use and that LDAC isn’t being negotiated.

- Check negotiated codec (when connected):
  ```bash
  pactl list sinks short
  bluetoothctl info <MAC>
  # or bluealsa-cli list-pcms (if using bluealsa)
  ```
- **PulseAudio limitation:** PA does not expose a config option to force SBC or disable LDAC per device. Many users report reconnection negotiates SBC XQ or LDAC and becomes choppy; first connection uses plain SBC and is fine. Workarounds: (1) **Switch to PipeWire** (section 5 and section 15) and set `bluez5.codecs=[sbc]`, or (2) **Remove LDAC support** — uninstall `pulseaudio-modules-bt` / `libldac` if you added them. (3) **USB BT dongle** (section 6) often negotiates more conservatively.

**Optional:** Some setups use **SBC-XQ** (higher SBC bitrate) for better quality without LDAC’s bandwidth; on a Pi Zero 2 W with WiFi on, plain SBC is often more stable.

---

## 3. PulseAudio: latency/buffer and profile cycling

**Cause:** Choppy A2DP can be buffer/latency related; sometimes the link gets into a bad state.

**Fix A — Port latency offset**  
Increase the A2DP port buffer (in microseconds). Example 50 ms. **The port name is device-dependent** — it may be `speaker-output`, `headset-output`, or something else; use the steps below to get the real name.

```bash
# 1. List cards and find the BlueZ card name and its Ports (while BT is connected)
pactl list cards

# 2. In the output, find the bluez_card.XX_XX_... block. Under "Ports:" you'll see lines like:
#    output: speaker-output: ...  OR  output: headset-output: ...
#    The port name is the part after "output: " and before the colon (e.g. speaker-output or headset-output).

# 3. Set latency offset (use YOUR card name and the port name from step 2; 50000 = 50 ms)
pactl set-port-latency-offset bluez_card.41_42_09_2A_4D_72 speaker-output 50000
# If that fails with "Invalid port", use the port name you saw (e.g. headset-output).

# 4. Restart Bluetooth to apply
sudo systemctl restart bluetooth
```

**One-liner to list BlueZ ports:**  
`pactl list cards | awk -v RS='' '/bluez_card/' | grep -E '^\s+Ports:|^\s+[a-z-]+:'` — look for the output port name under Ports.

Try 50000, 75000, or 100000 µs if 50 ms isn’t enough.

**Fix B — Profile cycle**  
If quality degrades mid-session, cycle the BT profile to resync:

```bash
BLUEZ_CARD="bluez_card.41_42_09_2A_4D_72"  # your device
pactl set-card-profile "$BLUEZ_CARD" a2dp
pactl set-card-profile "$BLUEZ_CARD" hsp
pactl set-card-profile "$BLUEZ_CARD" a2dp
```

Can be scripted and run when needed or after reconnect.

**Sources:** [Ask Ubuntu A2DP choppy](https://askubuntu.com/questions/475987/a2dp-on-pulseaudio-terrible-choppy-skipping-audio), [gpchelkin gist](https://gist.github.com/gpchelkin/b2fa4162272cfae4b5c0276237edd968).

---

## 4. WiFi power management

**Cause:** Aggressive WiFi power saving can create bursts of traffic and worsen BT timing.

**Fix:** Disable WiFi power save on the Pi (you already tried this; keep it off for BT audio):

```bash
# Check current
iwconfig wlan0 2>/dev/null | grep -i power

# Disable power management
sudo iwconfig wlan0 power off
```

To make it persistent, add a script or systemd unit that runs `iwconfig wlan0 power off` after boot or when wlan0 comes up.

---

## 5. PipeWire instead of PulseAudio (optional)

**Cause:** PipeWire often gives lower latency and more stable BT handling than PulseAudio on modern Linux.

**Fix:** On Raspberry Pi OS, if your image supports it, you can switch to PipeWire for audio (replacing PulseAudio). Then use PipeWire’s BT settings and codec options. This is a larger change (default device, user session, possibly megaphone.py output device), so only do it if firmware + SBC + buffer fixes aren’t enough.

**Source:** [PipeWire vs PulseAudio Bluetooth](https://huzi.pk/blog/tech/pipewire-vs-pulseaudio-bluetooth-latency), [PipeWire Bluetooth config](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html).

---

## 6. USB Bluetooth adapter (hardware fix)

**Cause:** Pi Zero 2 W has a single 2.4 GHz radio for both WiFi and BT; coexistence can only be improved so much in software.

**Fix:** Use a **USB Bluetooth adapter** (e.g. ~$8–15) so BT has its own radio and antenna. Disable the built-in BT or use the USB adapter as the only BT device for A2DP. WiFi stays on the built-in radio; BT audio uses the dongle → no shared-antenna interference.

---

## Recommended order of action

1. **Firmware:** `sudo apt update && sudo apt install firmware-brcm80211 && sudo reboot`. If still choppy, add the manual `btc_*` lines to the correct `brcmfmac43436*-sdio.txt`.
2. **Codec:** Ensure **SBC** is used (not LDAC) for the UGREEN sink.
3. **PulseAudio:** Set port latency offset (e.g. 50000–100000 µs) and restart Bluetooth; optionally script profile cycling if needed.
4. **WiFi:** Keep power management off: `iwconfig wlan0 power off` (and persist it).
5. If still not good enough: try **PipeWire** (if available) or a **USB Bluetooth adapter** for a dedicated BT radio.

---

## Quick reference

| Issue              | Fix                                              |
|--------------------|--------------------------------------------------|
| Phasing / dropouts | Firmware coexistence + SBC codec + PA buffer     |
| Choppy with WiFi   | `firmware-brcm80211` + `btc_*` in brcm file       |
| Still bad          | Port latency 50–100 ms, WiFi power off           |
| Last resort        | USB BT dongle or PipeWire                        |

---

## 7. PulseAudio daemon.conf: fragments and resampler

**Cause:** Default fragment size (25 ms × 4 = 100 ms total buffer) can be too small for BT on a busy Pi; resampling quality affects clarity.

**Fragment settings** (in `~/.config/pulse/daemon.conf` or `/etc/pulse/daemon.conf`; create a drop-in in `daemon.conf.d/` to avoid overwriting):

```ini
# Larger fragments = more buffer, less dropouts (at cost of latency)
default-fragments = 8
default-fragment-size-msec = 25
```

Default is 4 fragments × 25 ms = 100 ms. Try 8×25 (200 ms) or 6×50 (300 ms) for BT. Not all drivers honour this; timer-based drivers may ignore it.

**Resampler:** Default is `speex-float-1` (low CPU, lower quality). For cleaner resampling when PA converts sample rates for the BT sink:

```ini
resample-method = speex-float-5
# or speex-float-10 for best quality (more CPU)
```

Restart PulseAudio after changes (logout/login or `pulseaudio -k` in user session).

**Sources:** [pulse-daemon.conf(5)](https://manpages.debian.org/bullseye/pulseaudio/pulse-daemon.conf.5.en.html), [Freedesktop bug 104486](https://bugs.freedesktop.org/show_bug.cgi?id=104486).

---

## 8. Real-time scheduling and audio group

**Cause:** Audio threads missing real-time priority can cause jitter and dropouts under load.

**Fix:** Ensure the user running PulseAudio (and megaphone.py) has real-time priority. No RT kernel required.

1. Create/add to `/etc/security/limits.d/audio.conf`:
   ```
   @audio - rtprio 95
   @audio - memlock unlimited
   ```

2. Create group and add user (e.g. `midaswhale`):
   ```bash
   sudo groupadd -f audio
   sudo usermod -aG audio midaswhale
   ```

3. PulseAudio already uses `realtime-scheduling=yes` and `high-priority=yes` by default; ensure `rlimit-rtprio` in daemon.conf is at least 9 (default). For the megaphone service, you can set `Nice=-15` and optionally `CPUSchedulingPolicy=fifo` in the systemd unit if the user has rtprio.

**Sources:** [JACK FAQ Linux RT](https://jackaudio.org/faq/linux_rt_config.html), [Gentoo Realtime](https://wiki.gentoo.org/wiki/Project:Sound/How_to_Enable_Realtime_for_Multimedia_Applications).

---

## 9. CPU governor and core isolation (advanced)

**Cause:** Ondemand governor and CPU migration can introduce latency spikes; isolating a core for audio can reduce jitter.

**Governor:** Force performance governor so CPU doesn’t ramp during playback:
```bash
# Temporary
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Or install cpufrequtils and set in /etc/rc.local or a systemd unit
```

**Core isolation (optional):** Reserve one core for the audio path (e.g. PulseAudio or megaphone.py). Append to `/boot/cmdline.txt` (or `/boot/firmware/cmdline.txt` on Pi 5):
```
isolcpus=3
```
Then in the megaphone service file add `CPUAffinity=3` and `Nice=-15`. Reboot. Verify with `taskset -cp $(pidof pulseaudio)` and that the process runs on core 3.

**Note:** Pi Zero 2 W has 4 cores; isolating one leaves 3 for WiFi/API/LLM. Test; sometimes isolation helps more on Pi 4 than on Zero 2 W.

**Sources:** [raw-sewage Pi audio tuning](http://raw-sewage.net/articles/raspberry-pi-audio-tuning/), [linuxaudio.org RPi](https://wiki.linuxaudio.org/wiki/raspberrypi), [PiPedal latency](https://rerdavies.github.io/pipedal/AudioLatency.html).

---

## 10. BlueALSA instead of PulseAudio

**Cause:** PulseAudio adds a full sound server layer; BlueALSA talks BlueZ → ALSA directly, which can mean lower latency and fewer moving parts on a headless Pi.

**When to consider:** If you don’t need PA for other apps, BlueALSA is a common choice on Pi Lite. Raspberry Pi OS 12+ ships `bluez-alsa-utils`; on older OS install `bluealsa` and use ALSA device `bluealsa` with your app (e.g. point megaphone.py at an ALSA device instead of default Pulse).

**Setup (summary):**
```bash
sudo apt install bluealsa
sudo systemctl enable --now bluealsa
# Pair/connect device with bluetoothctl, then:
# /etc/asound.conf or ~/.asoundrc:
defaults.bluealsa {
    interface "hci0"
    device "41:42:09:2A:4D:72"
    profile "a2dp"
}
# Playback: aplay -D bluealsa /path/to/file.wav
```

You must disable or avoid loading PulseAudio’s Bluetooth modules if both are installed (conflict). Integration PA+BlueALSA is possible but “experimental” and has limitations.

**Sources:** [BlueALSA on headless Pi](https://introt.github.io/docs/raspberrypi/bluealsa.html), [BlueALSA README](https://github.com/Arkq/bluez-alsa), [RPi Stack Exchange](https://raspberrypi.stackexchange.com/questions/147602/bluetooth-audio-issue).

---

## 11. Disable built-in BT and use USB dongle only

**Cause:** Using a USB Bluetooth adapter avoids shared WiFi/BT antenna; disabling the built-in radio removes coexistence entirely for BT.

**Steps:**

1. Add to `/boot/config.txt` (or `/boot/firmware/config.txt` on Pi 5):
   ```
   dtoverlay=disable-bt
   ```
   (On Pi 5 some docs mention `disable-bt-pi5`; firmware often picks the right overlay.)

2. Disable the UART BT service:
   ```bash
   sudo systemctl stop hciuart
   sudo systemctl disable hciuart
   ```

3. Reboot. The USB dongle should appear as `hci0`. Pair and use it for A2DP as usual.

**Sources:** [RPi Forums disable BT use adapter](https://forums.raspberrypi.com/viewtopic.php?t=187658), [disable-bt overlay](https://raspberrypi.stackexchange.com/questions/147551/when-is-the-disable-bt-dtoverlay-necessary).

---

## 12. Physical placement and 2.4 GHz interference

**Cause:** BT and WiFi both use 2.4 GHz; they don’t coordinate. Distance and obstacles affect packet loss and audio glitches.

**Mitigations:**
- Keep Pi and UGREEN receiver **close** (e.g. 1–3 m) and with a clear line of sight where possible.
- Move the Pi away from dense WiFi (many APs, microwaves, etc.); use 5 GHz for other devices if your network allows so 2.4 GHz is less congested.
- Coexistence parameters (section 1) and SBC (section 2) help the radio deal with the same band; they don’t remove interference.

**Source:** [TI Bluetooth/WiFi coexistence](https://e2e.ti.com/support/wireless-connectivity/bluetooth-group/bluetooth/f/bluetooth-forum/772542/), [WiFi vs Bluetooth](https://electronics.stackexchange.com/questions/466798/does-bluetooth-interfere-with-wifi).

---

## 13. SBC-XQ and high-quality SBC (Moode / bluealsa)

**Cause:** Standard SBC is low bandwidth; SBC-XQ uses higher bitrate SBC for better quality without LDAC’s 2.4 GHz load. On Pi Zero 2 W, XQ+ can sometimes *increase* stutter (more data to send).

**If using BlueALSA / Moode-style stack:** Try disabling SBC-XQ or using `xq` instead of `xq+`. In Moode, editing `bluealsa` service to remove `--sbc-quality=xq+` or set `--sbc-quality=xq` improved stability for some users while keeping better-than-default SBC.

**PulseAudio:** SBC-XQ is more a bluez-alsa/ PipeWire option; PA’s module-bluetooth typically doesn’t expose SBC-XQ. For PA, focus on SBC vs LDAC (section 2) and buffer/latency (sections 3 and 7).

**Source:** [Moode forum SBC quality](https://moodeaudio.org/forum/showthread.php?tid=5607) (posts #9–10).

---

## 14. mSBC for voice (HSP/HFP) — not for megaphone A2DP

**Note:** mSBC is a **wideband voice** codec for headset/call profiles (HSP/HFP), not for A2DP music/playback. Your megaphone pipeline uses **A2DP** for playback, so mSBC doesn’t apply to the “phasing” output. It’s only relevant if you later add bidirectional voice (e.g. phone calls) over the same BT device.

**Source:** [Better Bluetooth headset with mSBC](https://www.redpill-linpro.com/techblog/2021/05/31/better-bluetooth-headset-audio-with-msbc.html).

---

## 15. PipeWire: force SBC-only (reliable codec control)

**Cause:** PulseAudio does not let you force SBC or disable LDAC per device. With PipeWire + WirePlumber you can restrict A2DP codecs so only SBC is used — fixes "choppy on reconnect" when the stack was negotiating SBC XQ or LDAC.

**When to use:** If you're willing to switch from PulseAudio to PipeWire on the Pi (or already on a distro that uses PipeWire), this is the clean way to guarantee SBC.

**WirePlumber config** (e.g. `/etc/wireplumber/wireplumber.conf.d/50-bluetooth-codecs.conf` or under your WirePlumber config directory):

```lua
monitor.bluez.properties = {
  ["bluez5.codecs"] = "[ sbc ]",
  ["bluez5.enable-sbc-xq"] = "false"
}
```

Or in the rules/style config (WirePlumber 0.5.x) the property is `bluez5.codecs` as an array; set it to `[ "sbc" ]` only. That disables LDAC, AAC, aptX, SBC-XQ, etc., so the device always negotiates plain SBC.

**Raspberry Pi:** PipeWire works on Pi; use a recent PipeWire/WirePlumber from Debian Bookworm+ (Pi OS Bullseye’s is often too old). See [Collabora: Pi as BT speaker with PipeWire](https://www.collabora.com/news-and-blog/blog/2022/09/02/using-a-raspberry-pi-as-a-bluetooth-speaker-with-pipewire-wireplumber/).

**Sources:** [Ask Ubuntu force SBC A2DP](https://askubuntu.com/questions/1456708/how-to-force-sbc-codec-on-a2dp-profile-on-ubuntu-22-04-bluetooth-audio) (answer: use PipeWire), [WirePlumber Bluetooth config](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html) (`bluez5.codecs`, `bluez5.enable-sbc-xq`).

---

## 16. Who initiates connection (PC vs headphone)

**Observation:** Some users report that when the **headphone/receiver initiates** the connection, the codec is SBC and audio is fine; when the **PC/Pi initiates**, the same device reconnects with SBC XQ or LDAC and audio is choppy. So the negotiation path can change the chosen codec.

**Workaround:** If you can, have the UGREEN (or headphone) initiate connect after boot (e.g. power it on after the Pi is up, or use a script that connects from the Pi but then cycles profile to force renegotiation). Alternatively force SBC via PipeWire (section 15) or USB dongle so behaviour is consistent.

**Source:** [Ask Ubuntu force SBC](https://askubuntu.com/questions/1456708/how-to-force-sbc-codec-on-a2dp-profile-on-ubuntu-22-04-bluetooth-audio) (comment: "When connection initiated from PC, codec is always sbc_xq_552 with choppy audio, but when initiated from the headphone, is sbc").

---

## Extended quick reference

| Area              | Action |
|-------------------|--------|
| Port latency      | Discover port with `pactl list cards` (Ports: output: **name**); use that name in `set-port-latency-offset` (often `speaker-output` or `headset-output`) |
| PA buffer         | `default-fragments = 8`, `default-fragment-size-msec = 25` in daemon.conf |
| Resampler         | `resample-method = speex-float-5` (or 10) in daemon.conf |
| Force SBC (PA)     | PA can't force SBC; use PipeWire + `bluez5.codecs=[sbc]`, or remove LDAC packages, or USB dongle |
| Force SBC (PipeWire)| WirePlumber: `bluez5.codecs = [ "sbc" ]`, `bluez5.enable-sbc-xq = false` |
| Connection init   | Choppy on PC-initiated reconnect: try headphone-initiated connect or PipeWire SBC-only |
| RT priority       | `@audio` group, `rtprio 95` in limits.d |
| CPU               | `performance` governor; optional `isolcpus=3` + CPUAffinity for audio |
| Alternative stack | BlueALSA (no PulseAudio) on headless Pi |
| USB dongle        | `dtoverlay=disable-bt`, disable `hciuart`, use USB as only BT |
| Placement         | Short distance, clear path, less 2.4 GHz congestion |
| SBC quality       | Prefer SBC over LDAC; if using BlueALSA/Moode, try `xq` not `xq+` |

---

## Next steps (from megaphone transcript)

If you came from the **Fixing Bluetooth Audio Quality.md** chat: firmware and btc params were already present; port latency failed because the port name wasn’t `speaker-output`. Recommended order:

1. **Discover port:** On the Pi with UGREEN connected, run `pactl list cards` and note the output port name under the bluez_card (e.g. `headset-output`).
2. **Set latency:** `pactl set-port-latency-offset bluez_card.41_42_09_2A_4D_72 <port_name> 75000` then `sudo systemctl restart bluetooth`.
3. **Reboot** so firmware/btc coexistence is fully applied.
4. Re-test with a continuous tone; if still phasey, try **PipeWire with SBC-only** (section 15) or a **USB Bluetooth adapter** (section 6).
