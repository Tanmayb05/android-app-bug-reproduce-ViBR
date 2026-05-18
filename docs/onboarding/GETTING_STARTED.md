# Getting Started with ViBR

This guide helps you navigate the ViBR project and get it running.

## What is ViBR?

**ViBR** (Vision-based Bug Replay) is an automated system that reproduces bugs from GUI video recordings using Vision-Language Models (VLMs) like GPT-4o.

**Key capabilities:**
- 📹 Segments video into user action scenes
- 🔍 Compares GUI states between recording and device
- 🎯 Detects interactive UI elements using GroundingDINO
- 🤖 Infers and replays actions using GPT-4o
- 📊 Achieves 72% reproducibility rate

## Quick Navigation

### I want to...

**Get started quickly (5 mins)**
→ Read [QUICKSTART.md](QUICKSTART.md)

**Do a full installation**
→ Read [SETUP.md](SETUP.md)

**Understand what was set up**
→ Read [SETUP_STATUS.md](SETUP_STATUS.md)

**Learn about the research**
→ Read [README.md](README.md)

**Understand the implementation**
→ Read [approach/README.md](approach/README.md)

**Run research evaluation**
→ Read [evaluation/README.md](evaluation/README.md)

**Troubleshoot issues**
→ See SETUP.md "Troubleshooting" section

## Current Status

### ✅ Completed Setup

Your environment is configured with:

- **Python 3.14.4** in virtual environment (`.venv/`)
- **All Python dependencies** installed:
  - PyTorch 2.12.0 (GPU/CPU support)
  - OpenAI SDK (GPT-4o integration)
  - GroundingDINO (object detection)
  - OpenCV, scikit-image, transformers, supervision
- **GroundingDINO** model weights (352 MB) downloaded
- **Comprehensive documentation** created

### ⚠️ Still Needed

To run ViBR, you still need:

1. **OpenAI API Key**
   - Get one: https://platform.openai.com/api-keys
   - Set it: `export OPENAI_API_KEY=sk-...`

2. **Android SDK & ADB** (if not already installed)
   - Follow SETUP.md section "5. Setup Android SDK and ADB"

3. **Android Device or Emulator**
   - Physical: Enable USB debugging, connect with USB cable
   - Emulator: Launch Android Emulator

## Run Your First Test

Once you have the prerequisites above:

```bash
# 1. Activate environment
cd /Users/tanmaybhuskute/Documents/ViBR
source .venv/bin/activate

# 2. Set API key
export OPENAI_API_KEY=sk-your-actual-key

# 3. Verify Android device is connected
adb devices

# 4. Run ViBR
python approach/segment_replay.py path/to/your/video.mp4
```

ViBR will:
- Show the starting state from your video
- Show the goal state
- Display live screenshots as it replays actions
- Report the final reproducibility status

## Project Structure

```
ViBR/
├── approach/               # Core implementation
│   ├── segment_replay.py   # ← Main entry point
│   ├── openai_api.py       # GPT-4o calls
│   ├── dino_detection.py   # GroundingDINO integration
│   ├── clip_seg.py         # Video segmentation
│   └── ...
│
├── evaluation/             # Research evaluation
│   ├── RQ1/               # Action segmentation evaluation
│   ├── RQ2/               # GUI state comparison evaluation
│   ├── RQ3/               # Bug replay evaluation
│   └── RQ4/               # Runtime overhead analysis
│
├── GroundingDINO/         # Submodule: object detection model
│   └── weights/
│       └── groundingdino_swint_ogc.pth  # ✓ Downloaded
│
├── .venv/                 # Virtual environment (created)
│
├── README.md              # Project overview & results
├── SETUP.md               # Full installation guide
├── QUICKSTART.md          # 5-minute quick start
├── SETUP_STATUS.md        # Setup status report
├── GETTING_STARTED.md     # This file
└── requirements.txt       # Python dependencies (all installed)
```

## Understanding ViBR

### How ViBR Works (High Level)

```
Input: GUI Screen Recording Video
   ↓
1. ACTION SEGMENTATION (CLIP)
   Split video into action scenes by comparing consecutive frames
   ↓
2. GUI STATE COMPARISON (GPT-4o + GroundingDINO)
   For each scene, verify if device's current GUI matches the recorded state
   ↓
3. INTERACTIVE REGION DETECTION (GroundingDINO)
   Identify buttons, text fields, and other interactive elements
   ↓
4. ACTION INFERENCE (GPT-4o)
   Determine what action to take (tap, swipe, type, etc.)
   ↓
5. ACTION EXECUTION (ADB)
   Execute the inferred action on the device
   ↓
Output: Reproducibility Rate & Execution Time
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **segment_replay.py** | Main orchestration | Python |
| **clip_seg.py** | Video segmentation | CLIP vision model |
| **dino_detection.py** | UI element detection | GroundingDINO |
| **openai_api.py** | Visual reasoning | GPT-4o API |
| **adb_device_controller.py** | Device automation | Android ADB |

## Important Notes

### Security
⚠️ **Never commit your OpenAI API key!**
- Use environment variables: `export OPENAI_API_KEY=sk-...`
- Or use `.env.example` as a template (copy to `.env`, add your key, don't commit)

### Costs
- **GPT-4o:** ~$0.02 per 10-action bug replay
- **GroundingDINO:** Free (local model, no API calls)
- **Android SDK/ADB:** Free

### Performance
- **Action Segmentation:** 30-50ms per frame
- **GUI State Comparison:** 4-5s per scene (includes GPT-4o)
- **Bug Replay:** 5-10s per action total
- **Typical 10-action bug:** 50-100 seconds + ~$0.02

## Common Questions

**Q: Can I use this on a physical Android phone?**
A: Yes! Enable USB debugging in Settings > Developer Options > USB Debugging, then connect via USB cable. ADB will detect it.

**Q: What video format does ViBR accept?**
A: MP4, MOV, AVI, and other formats supported by OpenCV (MPEG-4, H.264, etc.)

**Q: How accurate is ViBR?**
A: Achieves ~72% reproducibility rate compared to 45-50% for baseline methods.

**Q: Can I run this on CPU only?**
A: Yes, PyTorch will automatically use CPU if GPU isn't available (slower though).

**Q: Do I need the entire Android SDK?**
A: No, just the command-line tools and ADB. Full Android Studio is optional.

## Next Steps

1. **Set your OpenAI API key** (see SETUP.md)
2. **Install Android SDK** if needed (see SETUP.md)
3. **Connect an Android device** (physical or emulator)
4. **Run QUICKSTART.md** for your first test
5. **Explore the evaluation scripts** to reproduce research results

## Need Help?

- **Setup issues:** → SETUP.md "Troubleshooting"
- **How to run:** → QUICKSTART.md
- **Implementation details:** → approach/README.md
- **Research methodology:** → evaluation/README.md
- **Project overview:** → README.md

## Research Citation

ViBR is based on the following research:
- Paper: [to be added]
- Datasets: Available from Themis, GIFdroid, and V2S projects

## License

[Add appropriate license information]

---

**Ready to begin?** Start with [QUICKSTART.md](QUICKSTART.md)
