#!/usr/bin/env python3
"""Generate a QR code for https://grokandmon.com ."""
import sys
from pathlib import Path

def main():
    try:
        import qrcode
    except ImportError:
        print("Installing qrcode...", file=sys.stderr)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]"])
        import qrcode

    url = "https://grokandmon.com"
    out_dir = Path(__file__).resolve().parent.parent / "src" / "web" / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "grokandmon-qrcode.png"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)

    print(f"Saved: {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
