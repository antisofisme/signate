#!/usr/bin/env python3
"""
Test F12 hotkey detection
"""

print("\n" + "="*80)
print("⌨️  HOTKEY TEST - Press F12 to test")
print("="*80 + "\n")

print("[1] Testing pynput...")
try:
    from pynput import keyboard
    print("✅ pynput imported\n")
except ImportError as e:
    print(f"❌ pynput not installed: {e}\n")
    exit(1)

print("[2] Waiting for F12 hotkey...")
print("👉 Press F12 key (you have 10 seconds)\n")

pressed = False
released = False

def on_press(key):
    global pressed
    try:
        if key == keyboard.Key.f12:
            print("✅ F12 PRESSED!")
            pressed = True
    except AttributeError:
        pass

def on_release(key):
    global released
    try:
        if key == keyboard.Key.f12:
            print("✅ F12 RELEASED!")
            released = True
            return False  # Stop listener
    except AttributeError:
        pass

try:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join(timeout=10)

    print()
    if pressed and released:
        print("✅ F12 hotkey is working!")
    elif pressed:
        print("⚠️  F12 pressed detected, waiting for release...")
    else:
        print("❌ F12 key not detected")

except Exception as e:
    print(f"❌ Error: {e}\n")
    exit(1)

print("\n" + "="*80)
print("✅ HOTKEY TEST COMPLETE")
print("="*80 + "\n")
