# ViBR Quick Start

Get ViBR running in 5 minutes.

## 1. Activate Virtual Environment

```bash
cd /Users/tanmaybhuskute/Documents/ViBR
source .venv/bin/activate
```

## 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

Or edit `approach/openai_api.py` line 12:
```python
client = OpenAI(api_key="sk-your-key-here")
```

## 3. Connect Android Device/Emulator

```bash
adb devices
```

Should see:
```
emulator-5554          device
```

## 4. Prepare Your App

1. Launch the app in the emulator/device
2. Navigate to the starting state of your bug reproduction video
3. Have the video file ready

## 5. Run ViBR

```bash
python approach/segment_replay.py path/to/your/video.mp4
```

ViBR will display:
- ✓ Starting state
- ✓ Goal state  
- ✓ Live device screenshots as it replays actions
- ✓ Progress and status messages

## What Happens Next

ViBR automatically:
1. **Segments** the video into action scenes
2. **Compares** GUI states to verify consistency
3. **Detects** interactive regions using GroundingDINO
4. **Infers** user actions using GPT-4o
5. **Replays** actions on your device

## Troubleshooting

**"No module named groundingdino"**
```bash
cd GroundingDINO && pip install -e . --no-build-isolation && cd ..
```

**"adb: command not found"**
```bash
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

**"OpenAI API key not found"**
Make sure `OPENAI_API_KEY` environment variable is set:
```bash
echo $OPENAI_API_KEY  # Should not be empty
```

**Device not detected**
```bash
adb kill-server
adb devices
```

## Full Setup

For detailed instructions, see [SETUP.md](SETUP.md)

## Next Steps

- **Review results** in the console output
- **Check device screen** for replay progress
- **Test different apps** with ViBR

## Project Structure

```
ViBR/
├── .venv/              # Python virtual environment (created)
├── GroundingDINO/      # Object detection model
├── approach/           # Core implementation
├── evaluation/         # Research evaluation
├── README.md           # Project overview
├── SETUP.md            # Full setup guide
└── QUICKSTART.md       # This file
```

## Cost Estimate

- **Typical 10-action bug:** ~$0.02 (GPT-4o API)
- **GroundingDINO:** Free (local model)
- **ADB/Device:** Free

## Learn More

- [ViBR Paper](./README.md) — Full technical details
- [Approach](./approach/README.md) — Implementation details  
- [Evaluation](./evaluation/README.md) — Research methodology
