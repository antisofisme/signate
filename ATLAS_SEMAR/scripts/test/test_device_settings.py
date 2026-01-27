#!/usr/bin/env python3
"""
Test sounddevice with explicit device settings
"""

import numpy as np
import sounddevice as sd

print("\n" + "="*80)
print("🔧 TESTING SOUNDDEVICE WITH EXPLICIT SETTINGS")
print("="*80 + "\n")

print("Method 1: Using device index 1 (Logitech)")
print("Recording 3 seconds at 44100 Hz...\n")
print("SPEAK NOW!\n")

try:
    audio = sd.rec(
        int(3 * 44100),
        samplerate=44100,
        channels=1,
        dtype='int16',
        device=1,  # Explicit device index
        blocking=True
    )

    print(f"✅ Recording complete!")
    print(f"   Shape: {audio.shape}")
    print(f"   Min: {audio.min()}")
    print(f"   Max: {audio.max()}")
    print(f"   Range: [{audio.min()}, {audio.max()}]")
    print(f"   RMS: {np.sqrt(np.mean(audio**2)):.2f}")

    if np.max(np.abs(audio)) < 100:
        print("\n❌ STILL VERY QUIET!")
        print("   Device might have automatic gain control or be muted")
    else:
        print("\n✅ GOOD SIGNAL!")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80 + "\n")
