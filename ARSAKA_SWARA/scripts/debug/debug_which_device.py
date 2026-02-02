#!/usr/bin/env python3
"""
Check which device sounddevice.rec() uses
"""

import sounddevice as sd

print("\n" + "="*80)
print("🔍 WHICH DEVICE IS BEING USED?")
print("="*80 + "\n")

print("Default devices:")
print(f"  Input (rec): {sd.default.device[0]}")
print(f"  Output (play): {sd.default.device[1]}\n")

if sd.default.device[0] is not None:
    device_info = sd.query_devices(sd.default.device[0])
    print(f"Default Input Device: {device_info['name']}")
    print(f"  Channels: {device_info['max_input_channels']}")
    print(f"  Sample rate: {device_info['default_samplerate']}")
else:
    print("No default input device!")

print("\n" + "="*80 + "\n")
