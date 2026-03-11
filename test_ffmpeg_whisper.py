# test_ffmpeg_whisper.py
import subprocess
import whisper
import tempfile
import os

print("🔍 System Check")
print("=" * 50)

# 1. Check FFmpeg
print("1. Checking FFmpeg...")
try:
    result = subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, 
                          text=True, 
                          shell=True)
    if result.returncode == 0:
        print("   ✅ FFmpeg is working!")
        # Extract version
        for line in result.stdout.split('\n'):
            if 'ffmpeg version' in line:
                print(f"   Version: {line[:50]}")
                break
    else:
        print("   ❌ FFmpeg not found")
except Exception as e:
    print(f"   ❌ FFmpeg error: {e}")

# 2. Check Whisper
print("\n2. Checking Whisper...")
try:
    model = whisper.load_model("tiny")
    print("   ✅ Whisper is working!")
    
    # Create a test audio file (silence)
    import numpy as np
    import soundfile as sf
    
    # Generate 1 second of silence
    sample_rate = 16000
    silence = np.zeros(sample_rate)
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        sf.write(f.name, silence, sample_rate)
        
        # Try to transcribe
        result = model.transcribe(f.name)
        print(f"   ✅ Can process audio files")
        
        os.unlink(f.name)
        
except Exception as e:
    print(f"   ❌ Whisper error: {e}")

# 3. Check Python environment
print("\n3. Checking Python environment...")
import sys
print(f"   Python: {sys.version.split()[0]}")
print(f"   Virtual env: {'venv' in sys.executable}")

print("\n" + "=" * 50)
print("✅ System check complete!")
input("Press Enter to run Streamlit app...")

# Launch Streamlit
print("\n🚀 Launching Streamlit app...")
subprocess.run(['streamlit', 'run', 'streamlit_app_working.py'])