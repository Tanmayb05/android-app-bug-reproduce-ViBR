# ViBR Setup Checklist

## ✅ Completed by Claude Code

- [x] Created Python virtual environment (.venv)
- [x] Installed all Python dependencies (30+ packages)
- [x] Cloned GroundingDINO repository
- [x] Installed GroundingDINO with correct build flags
- [x] Downloaded model weights (352 MB)
- [x] Created SETUP.md (comprehensive installation guide)
- [x] Created QUICKSTART.md (5-minute guide)
- [x] Created SETUP_STATUS.md (status report)
- [x] Created GETTING_STARTED.md (navigation guide)
- [x] Created .env.example (configuration template)
- [x] Verified all installations working

## ⚠️ Still Needed by You

### 1. OpenAI API Key (Required to run ViBR)
- [ ] Visit https://platform.openai.com/api-keys
- [ ] Create a new API key
- [ ] Copy the key (starts with `sk-`)
- [ ] Set environment variable: `export OPENAI_API_KEY=sk-your-key`
- [ ] Or edit `approach/openai_api.py` line 12 with your key

### 2. Android SDK Installation (Required to run ViBR)
- [ ] Download Android SDK command-line tools
- [ ] Extract to your desired location
- [ ] Set ANDROID_HOME environment variable
- [ ] Install platform-tools, platforms;android-30, build-tools;30.0.3
- [ ] Verify adb works: `adb version`
- [ ] See SETUP.md section 5 for detailed instructions

### 3. Android Device Connection (Required to run ViBR)
- [ ] **Physical device option:**
  - [ ] Enable USB Debugging (Settings > Developer Options)
  - [ ] Connect device via USB cable
  - [ ] Verify: `adb devices` (should show your device)
- [ ] **Emulator option:**
  - [ ] Launch Android Emulator from Android Studio
  - [ ] Verify: `adb devices` (should show emulator-5554)

## 🚀 Ready to Run

Once you complete items 1-3 above, you can run:

```bash
cd /Users/tanmaybhuskute/Documents/ViBR
source .venv/bin/activate
export OPENAI_API_KEY=sk-your-actual-key
python approach/segment_replay.py path/to/your/video.mp4
```

## 📚 Documentation to Read

### Start Here
- [ ] QUICKSTART.md — 5-minute quick start guide

### Then Read
- [ ] GETTING_STARTED.md — Navigation and FAQ
- [ ] SETUP_STATUS.md — Verify current setup state
- [ ] SETUP.md — Full installation details if you hit issues

### Optional (For Understanding)
- [ ] README.md — Project overview and research results
- [ ] approach/README.md — Technical implementation details
- [ ] evaluation/README.md — Research evaluation methodology

## 🔍 Verification Commands

After completing all items, verify everything works:

```bash
# 1. Environment is ready
cd /Users/tanmaybhuskute/Documents/ViBR
source .venv/bin/activate

# 2. Dependencies work
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import openai; print('OpenAI SDK: OK')"
python3 -c "import groundingdino; print('GroundingDINO: OK')"

# 3. Model weights exist
ls -lh GroundingDINO/weights/groundingdino_swint_ogc.pth

# 4. Android device is connected
adb devices

# 5. API key is set
echo $OPENAI_API_KEY  # Should NOT be empty
```

All commands should succeed without errors.

## 🆘 Troubleshooting

If you encounter issues:

1. **Environment errors?** → See SETUP.md "Troubleshooting"
2. **Android setup issues?** → See SETUP.md section 5
3. **Running ViBR?** → See QUICKSTART.md
4. **Don't know where to start?** → Read GETTING_STARTED.md

## 📞 Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: groundingdino` | `cd GroundingDINO && pip install -e . --no-build-isolation` |
| `adb: command not found` | Add `$ANDROID_HOME/platform-tools` to PATH |
| `OpenAI API Error` | Check `echo $OPENAI_API_KEY` is not empty and valid |
| `no devices found` | Run `adb kill-server && adb devices` |

## 💾 Files Created

**Documentation:**
- SETUP.md — Full installation guide
- QUICKSTART.md — Quick start
- SETUP_STATUS.md — Setup status
- GETTING_STARTED.md — Navigation
- CHECKLIST.md — This file
- .env.example — Config template

**Virtual Environment:**
- .venv/ — Python environment (created)

**Model & Dependencies:**
- GroundingDINO/ — Object detection model
- GroundingDINO/weights/ — Model weights (352 MB)

## ✨ Next Steps

1. [ ] Read QUICKSTART.md
2. [ ] Get OpenAI API key
3. [ ] Install Android SDK
4. [ ] Connect Android device
5. [ ] Run first test: `python approach/segment_replay.py sample-video.mp4`

---

**Everything is ready for you to complete the final steps!**

See QUICKSTART.md to begin using ViBR.
