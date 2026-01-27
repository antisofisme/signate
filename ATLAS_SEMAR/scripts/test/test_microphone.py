#!/usr/bin/env python3
"""
Test microphone - untuk lihat apakah mic terdeteksi
"""

print("\n" + "="*80)
print("🎤 MICROPHONE TEST")
print("="*80 + "\n")

print("[1] Testing sounddevice...")
try:
    import sounddevice as sd
    print("✅ sounddevice imported\n")
except ImportError as e:
    print(f"❌ sounddevice not installed: {e}\n")
    exit(1)

print("[2] Listing audio devices...")
print()
try:
    devices = sd.query_devices()
    print(f"Found {len(devices)} audio devices:\n")
    for i, device in enumerate(devices):
        print(f"[{i}] {device['name']}")
        print(f"    Channels: {device['max_input_channels']} in, {device['max_output_channels']} out")
        if i == sd.default.device[0]:
            print(f"    ⭐ DEFAULT INPUT")
        if i == sd.default.device[1]:
            print(f"    ⭐ DEFAULT OUTPUT")
        print()
except Exception as e:
    print(f"❌ Error listing devices: {e}\n")
    exit(1)

print("[3] Testing default microphone...")
try:
    default_input = sd.default.device[0]
    device_info = sd.query_devices(default_input)
    print(f"Default microphone: {device_info['name']}")
    print(f"Channels: {device_info['max_input_channels']}")

    if device_info['max_input_channels'] > 0:
        print("✅ Microphone is available!\n")
    else:
        print("❌ Default device has no input channels\n")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}\n")
    exit(1)

print("[4] Recording 3 seconds test...")
print("🎤 Speak now... (3 seconds)")
try:
    import numpy as np

    duration = 3  # seconds
    sample_rate = 16000

    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()

    # Check if any sound was captured
    max_level = np.max(np.abs(audio))
    print(f"✅ Recording complete!")
    print(f"   Max audio level: {max_level:.4f}")

    if max_level > 0.01:
        print("   ✅ Microphone is working! (detected sound)")
    else:
        print("   ⚠️  No sound detected (might be too quiet or mic issue)")

except Exception as e:
    print(f"❌ Recording failed: {e}\n")
    exit(1)

print("\n" + "="*80)
print("✅ MICROPHONE TEST COMPLETE")
print("="*80 + "\n")
