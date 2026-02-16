#!/usr/bin/env python3
"""
Test RVC voice conversion with Mr.Bomboclaut Jamaican model
"""

import os
import asyncio
from pathlib import Path

# Test edge-tts first
async def test_edge_tts():
    import edge_tts

    text = "Wah gwaan, I and I cultivating di herb. Jah bless, one love!"
    voice = "en-US-GuyNeural"  # Male voice for base
    output_file = Path(__file__).parent / "test_tts_output.wav"

    print(f"[TTS] Generating speech with edge-tts...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_file))
    print(f"[TTS] Saved to: {output_file}")
    return output_file

# Test RVC conversion
def test_rvc(input_file: Path):
    from rvc_python.infer import RVCInference

    model_path = Path(__file__).parent / "rvc_models" / "Mr.Bomboclaut.pth"
    index_path = Path(__file__).parent / "rvc_models" / "added_IVF126_Flat_nprobe_1_Mr.Bomboclaut_v2.index"
    output_file = Path(__file__).parent / "test_rvc_output.wav"

    print(f"[RVC] Loading model: {model_path.name}")

    # Initialize RVC (CPU since RTX 5070 Ti sm_120 not yet supported by PyTorch)
    rvc = RVCInference(device="cpu")
    rvc.load_model(str(model_path), index_path=str(index_path))

    print(f"[RVC] Converting voice...")
    rvc.infer_file(str(input_file), str(output_file))

    print(f"[RVC] Saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    print("=" * 50)
    print("Testing RVC Pipeline")
    print("=" * 50)

    # Step 1: Generate TTS
    tts_file = asyncio.run(test_edge_tts())

    # Step 2: Convert with RVC
    rvc_file = test_rvc(tts_file)

    print("\n[DONE] Test complete!")
    print(f"Original TTS: {tts_file}")
    print(f"RVC Converted: {rvc_file}")
