# Chromebook Server — Full Specs

Production server for Grok & Mon (plant ops, unified agent, HAL API). Boots Ubuntu from external drive.

| Item | Value |
|------|--------|
| **Hostname** | chromebook |
| **LAN** | chromebook.lan |
| **SSH** | `ssh natha@chromebook.lan` |
| **Board codename** | Cave |

---

## CPU

| Spec | Value |
|------|--------|
| **Model** | Intel Core m3-6Y30 @ 0.90 GHz |
| **Cores / threads** | 2 cores, 4 threads |
| **Architecture** | x86_64 |
| **Frequency** | Min 400 MHz, max 2200 MHz (base 0.90 GHz) |
| **GPU** | Integrated Intel HD Graphics 515 (Skylake) |

---

## Memory

| Spec | Value |
|------|--------|
| **RAM (total)** | 3.7 GiB (4 GB physical; ~300 MB reserved for GPU/firmware) |
| **Swap** | 2.0 GiB |

*Typical usage: ~1.9 GiB used, ~1.8–1.9 GiB available with grokmon + OpenClaw + trading agent running.*

---

## Storage

| Spec | Value |
|------|--------|
| **Root filesystem** | /dev/sda3 on external drive |
| **Size** | 59 GiB total |
| **Used** | ~35 GiB (~62%) |
| **Available** | ~22 GiB |

---

## OS & Kernel

| Spec | Value |
|------|--------|
| **OS** | Ubuntu 24.04 LTS (Noble) |
| **Kernel** | 6.8.0-90-generic |
| **Boot** | From external drive (not internal eMMC) |

---

## Network & Identity

| Spec | Value |
|------|--------|
| **MAC address** | d4:25:8b:41:41:d2 |
| **Public access** | Cloudflare Tunnel → grokandmon.com, agent.grokandmon.com |

---

## Services (typical)

- **grokmon.service** — FastAPI (HAL) :8000, OpenClaw gateway :18789, trading agent :8001
- **ganja-mon-bot.service** — Telegram @MonGardenBot
- **earlyoom** — Kills runaway processes before OOM

Kiosk and retake-stream are disabled by default to avoid OOM on 3.7 GB RAM.

---

*Specs gathered 2026-02-12 via SSH (`lscpu`, `free -h`, `df`, `lsb_release`, `uname`, DMI).*
