"""
Camera Diagnostic Tool - Identifies available camera devices on the system.

Run this to find the correct camera index for your system:
  python -m src.camera_diagnostic
"""

import sys

try:
    import cv2
except ImportError:
    print("[Error] OpenCV is not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

import time


def diagnose_cameras(max_index: int = 10) -> None:
    """Probes camera indices 0-9 and reports which ones are available."""
    print("=" * 70)
    print("AI GESTURE MOUSE - CAMERA DIAGNOSTIC TOOL")
    print("=" * 70)
    print()
    
    working_cameras = []
    
    for idx in range(max_index):
        print(f"[Test {idx}] Attempting cv2.VideoCapture({idx})...", end=" ", flush=True)
        
        try:
            cap = cv2.VideoCapture(idx)
            
            if cap is None:
                print("❌ Returned None")
                continue
            
            is_opened = cap.isOpened()
            
            if not is_opened:
                print("❌ Not opened")
                cap.release()
                continue
            
            # Try to read a frame
            print("✓ Opened. Reading frame...", end=" ", flush=True)
            ret, frame = cap.read()
            
            if not ret or frame is None or frame.size == 0:
                print("❌ Cannot read frame")
                cap.release()
                continue
            
            # Get frame properties
            h, w = frame.shape[:2]
            print(f"✓ SUCCESS - Frame size: {w}x{h}")
            
            working_cameras.append((idx, w, h))
            cap.release()
            time.sleep(0.5)  # Give camera time to reset
            
        except Exception as e:
            print(f"❌ Exception: {str(e)[:50]}")
            try:
                cap.release()
            except:
                pass
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if working_cameras:
        print(f"\n✓ Found {len(working_cameras)} working camera(s):\n")
        for idx, w, h in working_cameras:
            print(f"   Camera #{idx}  →  Resolution: {w}x{h}")
        
        print()
        print("To use a specific camera, run:")
        for idx, w, h in working_cameras:
            print(f"   python src/main.py --camera {idx}")
    else:
        print("\n❌ NO CAMERAS FOUND")
        print()
        print("Troubleshooting steps:")
        print("  1. Check that your webcam is connected and powered on")
        print("  2. Open Windows Camera app to verify it works")
        print("  3. Check for other apps using the camera (close them first)")
        print("  4. Restart your computer and try again")
        print("  5. Update or reinstall camera drivers")
        print()
        print("If this still fails, the camera may not be recognized by OpenCV.")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    diagnose_cameras()
