# ViBR Setup Guide

ViBR is an automated bug replay system using Vision-Language Models to reproduce bugs from GUI video recordings.

## Prerequisites

- **macOS/Linux/Windows**
- **Java Development Kit (JDK)** — required for Android SDK
- **Git** — for cloning repositories

## Installation Steps

### 1. Create Python Virtual Environment

```bash
cd /path/to/ViBR
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- `opencv-python` — image/video processing
- `openai` — GPT-4o API integration
- `scikit-image` — advanced image analysis
- `torch` & `torchvision` — deep learning models
- `transformers` — NLP models
- `supervision` — computer vision utilities

### 3. Install and Setup GroundingDINO

GroundingDINO is an object detection model used to identify interactive UI regions.

```bash
# Clone GroundingDINO repository
git clone https://github.com/IDEA-Research/GroundingDINO.git

# Install GroundingDINO
cd GroundingDINO
pip install -e . --no-build-isolation
cd ..

# Create weights directory and download model (GroundingDINO-B)
mkdir -p GroundingDINO/weights
cd GroundingDINO/weights
curl -L https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth -o groundingdino_swint_ogc.pth
cd ../..
```

**Note:** The model weights file is ~661MB. Download may take a few minutes.

### 4. Configure OpenAI API Key

You'll need an OpenAI API key to use GPT-4o for visual reasoning.

**Option A: Environment Variable (Recommended)**
```bash
export OPENAI_API_KEY=sk-your-key-here
```

**Option B: Update Code**
Edit `approach/openai_api.py` (line 12):
```python
client = OpenAI(api_key="sk-your-key-here")
```

⚠️ **WARNING:** Never commit API keys to version control. Use environment variables in production.

### 5. Setup Android SDK and ADB

#### macOS/Linux:

1. Download Android SDK command-line tools:
   ```bash
   mkdir -p ~/Android/sdk
   cd ~/Android/sdk
   curl -o cmdline-tools.zip https://developer.android.com/studio
   unzip cmdline-tools.zip
   ```

2. Set environment variables:
   ```bash
   # Add to ~/.bashrc, ~/.zshrc, or ~/.bash_profile
   export ANDROID_HOME=$HOME/Android/sdk
   export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
   ```

3. Install SDK packages:
   ```bash
   $ANDROID_HOME/cmdline-tools/bin/sdkmanager "platform-tools" "platforms;android-30" "build-tools;30.0.3"
   ```

#### Windows:

1. Download Android SDK from [Android Developer Site](https://developer.android.com/studio/index.html#command-tools)
2. Extract to a directory (e.g., `C:\android-sdk`)
3. Set environment variables:
   - Add `ANDROID_HOME=C:\android-sdk`
   - Add to PATH: `%ANDROID_HOME%\tools;%ANDROID_HOME%\platform-tools`
4. Run `sdkmanager.bat` to install platform tools

### 6. Connect Android Device/Emulator

**For Physical Device:**
- Enable USB debugging: Settings > Developer Options > USB Debugging
- Connect via USB cable
- Verify: `adb devices`

**For Emulator:**
- Launch Android Emulator
- Check: `adb devices` (should show `emulator-5554` or similar)

**Verify Connection:**
```bash
adb devices
```

Output should show:
```
List of attached devices
emulator-5554          device
```

## Project Structure

```
ViBR/
├── approach/                 # Core ViBR implementation
│   ├── segment_replay.py     # Main execution script
│   ├── clip_seg.py           # Action segmentation using CLIP
│   ├── dino_detection.py     # GroundingDINO integration
│   ├── openai_api.py         # GPT-4o API calls
│   ├── adb_device_controller.py  # ADB device interaction
│   └── ...
├── evaluation/               # Research evaluation scripts
│   ├── RQ1/                  # Action segmentation evaluation
│   ├── RQ2/                  # GUI state comparison evaluation
│   ├── RQ3/                  # Bug replay evaluation
│   └── RQ4/                  # Runtime overhead analysis
├── GroundingDINO/           # GroundingDINO submodule
│   └── weights/
│       └── groundingdino_swint_ogc.pth
├── requirements.txt         # Python dependencies
└── SETUP.md                 # This file
```

## Running ViBR

### Quick Start

1. **Prepare your device/emulator:**
   - App should be installed and running
   - Navigate to the initial state where you recorded the video

2. **Run ViBR:**
   ```bash
   source .venv/bin/activate
   python approach/segment_replay.py <path_to_video.mp4>
   ```

3. **Monitor execution:**
   - ViBR will display:
     - Start and goal states
     - Live screenshots from device
     - Current replay progress
   - Check console output for any errors

### Example

```bash
source .venv/bin/activate
python approach/segment_replay.py videos/AmazeFileManager-1558.mp4
```

## Running Evaluation

The evaluation directory contains scripts to reproduce the research results.

### RQ1: Action Segmentation
```bash
python evaluation/RQ1/run_rq1.py --video dataset/FirefoxLite-4881/video-#4881.mp4 --method gifdroid
```

### RQ2: GUI State Comparison
```bash
python evaluation/RQ2/run_rq2.py
```

### RQ3: Bug Replay
```bash
python evaluation/RQ3/run_rq3.py --video dataset/FirefoxLite-4881/video-#4881.mp4
```

### RQ4: Runtime Overhead
```bash
python evaluation/RQ4/run_rq4.py
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'groundingdino'`
**Solution:** Ensure GroundingDINO is installed:
```bash
cd GroundingDINO
pip install -e . --no-build-isolation
cd ..
```

### Issue: `adb: command not found`
**Solution:** Add Android SDK to PATH:
```bash
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

### Issue: No devices detected
**Solution:** Check device connection:
```bash
adb devices
adb kill-server
adb devices  # Restart ADB
```

### Issue: OpenAI API errors
**Solution:** Verify API key and account:
```bash
export OPENAI_API_KEY=sk-your-actual-key
```

### Issue: GroundingDINO weights not found
**Solution:** Ensure weights are in correct location:
```bash
ls -lh GroundingDINO/weights/groundingdino_swint_ogc.pth
```

## Performance Notes

- **Action Segmentation:** ~30-50ms per frame on M1/M2 Macs
- **GUI State Comparison:** ~4-5s per frame (includes GPT-4o calls)
- **Bug Replay:** ~5-10s per action including device execution
- **Total cost:** ~$0.02 per 10-action sequence with GPT-4o

## Documentation

- **Main README:** `README.md` — Project overview and results
- **Approach Details:** `approach/README.md` — Implementation details
- **Evaluation:** `evaluation/README.md` — Research methodology

## Support

For issues with:
- **GroundingDINO:** See [IDEA-Research/GroundingDINO](https://github.com/IDEA-Research/GroundingDINO)
- **Android SDK:** See [Android Developer Documentation](https://developer.android.com/studio)
- **OpenAI API:** See [OpenAI Documentation](https://platform.openai.com/docs)
