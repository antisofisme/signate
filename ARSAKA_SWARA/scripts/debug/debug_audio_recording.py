#!/usr/bin/env python3
"""
Debug script - lihat apa yang sebenarnya direcord
"""

import numpy as np
import sounddevice as sd

print("\n" + "="*80)
print("🔍 AUDIO RECORDING DEBUG")
print("="*80 + "\n")

print("[1] Testing direct sounddevice.rec()...\n")

print("Recording 3 seconds of audio...")
print("SPEAK NOW!\n")

duration = 3
sample_rate = 16000
audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
sd.wait()

print(f"\n✅ Recording complete!")
print(f"   Shape: {audio.shape}")
print(f"   Dtype: {audio.dtype}")
print(f"   Min value: {audio.min()}")
print(f"   Max value: {audio.max()}")
print(f"   Mean value: {audio.mean()}")
print(f"   RMS: {np.sqrt(np.mean(audio**2))}")

# Check if all zeros
if np.all(audio == 0):
    print("\n❌ ALL ZEROS! Microphone not recording!")
elif np.max(np.abs(audio)) < 100:
    print(f"\n⚠️  VERY QUIET (max amplitude: {np.max(np.abs(audio))})")
    print("   Try speaking LOUDER!")
elif np.max(np.abs(audio)) < 1000:
    print(f"\n⚠️  QUIET (max amplitude: {np.max(np.abs(audio))})")
    print("   Try speaking louder")
else:
    print(f"\n✅ GOOD SIGNAL (max amplitude: {np.max(np.abs(audio))})")

print("\n" + "="*80 + "\n")
