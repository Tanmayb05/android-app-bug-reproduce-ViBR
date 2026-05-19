# Issues Log

Each section = one run, identified by timestamp and config.

---

## 2026-05-18 17:56 — app: adaway | quality: bad | algo: clip | provider: gemini

### CRITICAL — RuntimeError: httpx client closed (FIXED)

**File:** `approach/providers/gemini_provider.py:40`
**Symptom:** Crash at `ask_gpt_for_relevant_regions` → `gemini_provider.ask` → `genai.Client.generate_content`
```
RuntimeError: Cannot send a request, as the client has been closed.
```
**Cause:** `genai.Client()` constructed per-call. On Python 3.14, GC closes the internal httpx client before the request resolves.
**Fix:** Module-level singleton `_client_instance` keyed by api_key. Applied.

---

### WARNING — Unauthenticated HuggingFace requests (FIXED)

**Symptom:**
```
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
```
**Cause:** `HF_TOKEN` in `.env.local` not loaded before CLIP model download.
**Fix:** `_load_dotenv()` called early in `main()` before CLIP loads. Applied.

---

### WARNING — `torch.meshgrid` missing `indexing` argument (FIXED)

**Files:**
- `GroundingDINO/groundingdino/util/box_ops.py:121`
- `GroundingDINO/groundingdino/models/GroundingDINO/utils.py:79`
- `GroundingDINO/groundingdino/models/GroundingDINO/transformer.py:470`
- `GroundingDINO/groundingdino/models/GroundingDINO/backbone/swin_transformer.py:116`

**Symptom:** `UserWarning: torch.meshgrid: in an upcoming release, it will be required to pass the indexing argument.`
**Fix:** Added `indexing="ij"` to all 4 calls. Applied.

---

### WARNING — `torch.cuda.amp.autocast` deprecated (FIXED)

**File:** `GroundingDINO/groundingdino/models/GroundingDINO/transformer.py:862`
**Symptom:** `FutureWarning: torch.cuda.amp.autocast(args...) is deprecated.`
**Fix:** Changed to `torch.amp.autocast("mps", enabled=False)` (device: Apple MPS). Applied.

---

### WARNING — `torch.utils.checkpoint` missing `use_reentrant` (FIXED)

**Files:**
- `GroundingDINO/groundingdino/models/GroundingDINO/transformer.py:551` (fusion layers)
- `GroundingDINO/groundingdino/models/GroundingDINO/transformer.py:576` (main transformer)
- `GroundingDINO/groundingdino/models/GroundingDINO/backbone/swin_transformer.py:448`

**Symptom:** `UserWarning: torch.utils.checkpoint: the use_reentrant parameter should be passed explicitly. Starting in PyTorch 2.9, calling checkpoint without use_reentrant will raise an exception.`
**Fix:** Added `use_reentrant=False` to all 3 calls. Applied.

---

### WARNING — `use_return_dict` deprecated in transformers (FIXED)

**File:** `GroundingDINO/groundingdino/models/GroundingDINO/bertwarper.py:100`
**Symptom:** `FutureWarning: use_return_dict is deprecated! Use return_dict instead!`
**Fix:** Changed `self.config.use_return_dict` → `self.config.return_dict`. Applied.

---

### INFO — BERT UNEXPECTED weight keys (NOT FIXED — benign)

**File:** GroundingDINO BERT encoder load
**Symptom:**
```
cls.predictions.bias                       | UNEXPECTED
cls.predictions.transform.LayerNorm.bias   | UNEXPECTED
cls.predictions.transform.dense.bias       | UNEXPECTED
cls.seq_relationship.bias                  | UNEXPECTED
cls.predictions.transform.dense.weight     | UNEXPECTED
cls.predictions.transform.LayerNorm.weight | UNEXPECTED
cls.seq_relationship.weight                | UNEXPECTED
```
**Cause:** Full MLM checkpoint (`bert-base-uncased`) loaded into backbone-only encoder. MLM head keys are unused/unexpected.
**Status:** Benign — model works correctly. GroundingDINO only uses the encoder layers, not the MLM head.

---

### INFO — Many HuggingFace 404s during CLIP model load (NOT FIXED — benign)

**Symptom:** Multiple HEAD requests returning 404 for `model.safetensors`, `processor_config.json`, `chat_template.json`, etc.
**Cause:** `transformers` probes for multiple file formats/configs before falling back to `pytorch_model.bin`. Expected behavior.
**Status:** Benign — model loads successfully via fallback path.

---

## 2026-05-18 18:20 — app: adaway | quality: bad | algo: clip | provider: gemini

### CRITICAL — JSONDecodeError on empty LLM response (FIXED)

**File:** `approach/segment_replay.py:69` (extract_json)
**Symptom:** Crash at segment 1: `ask_gpt_for_relevant_regions` returns empty/non-JSON string → `extract_json` → `json.JSONDecodeError`
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```
**Cause:** LLM returned empty response; `extract_json` called `.strip()` and `json.loads()` with no guard for empty/non-JSON input.
**Fix:** Added empty-string guard at start of `extract_json`. Added regex fallback to extract first `{...}` block if top-level parse fails. Applied.

---

### UX — Manual blocking prompts per segment (FIXED)

**Files:** `approach/segment_replay.py:431-435` (show_images), `approach/segment_replay.py:541` (input)
**Symptom:** Two blocking prompts per segment:
1. `show_images()` at line 431 → cv2 window waiting for keypress
2. `input("Press Enter to continue...")` at line 541 → terminal stdin block
This required manual intervention after every segment, preventing unattended runs.
**Fix:** Removed both blocking calls. Images already saved to disk as `dino.png`, `labeled.png`, `relevant_regions.png`. Applied.

---

### UX — Output images scattered in temp/, not in app artifacts dir (FIXED)

**File:** `approach/segment_replay.py:321-325`
**Symptom:** Per-segment outputs (DINO, XML labels, relevant regions) saved to `temp/<video_stem>/step_<i>/` instead of app-specific location. Hard to locate artifacts after run.
**Cause:** Output dir set to temp root by default.
**Fix:** Changed output path from `Path("temp") / video_stem / f"step_{i}"` to `Path("apps") / app_name / f"{quality}-artifacts" / f"step_{i}"`. All downstream saves automatically use new path. Applied.

---

## 2026-05-18 18:57 — app: adaway | quality: good | algo: clip | provider: gemini

### CRITICAL — TypeError: list used as dict key for LLM region (FIXED)

**File:** `approach/segment_replay.py:488`
**Symptom:** Crash during recovery action resolution:
```
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')
```
**Cause:** Gemini returned `region` as a list, but replay code assumed a scalar integer and checked membership in `region_index_to_center`.
**Fix:** Added LLM response normalization for scalar/list/string region values. Multiple regions are collapsed to the first valid index with a warning. Applied.

---

### CRITICAL — Missing action schema validation before execution (FIXED)

**Files:** `approach/segment_replay.py`, `approach/execute_action.py`
**Symptom:** Replay could call `execute_actions()` with malformed actions, e.g. tap without `position`, swipe without `from`/`to`, or unknown action names.
**Cause:** Raw LLM JSON was passed directly into action resolution/execution with no contract check.
**Fix:** Added `normalize_action_response()` and `action_is_executable()`. Invalid actions are skipped with a warning instead of crashing or executing partial input. Applied.

---

### BUG — DINO region indices mixed with XML element indices (FIXED)

**File:** `approach/segment_replay.py`
**Symptom:** Selected relevant regions were annotated from DINO detections, but action coordinates were resolved using XML-derived region indices.
**Cause:** DINO detections and Android XML elements have separate index spaces. Region `7` in DINO is not guaranteed to match region `7` in XML.
**Fix:** Replay actions now resolve highlighted region indices against DINO centers. Recovery actions still resolve against the live XML-labeled screen. Applied.

---

### BUG — Recovery loop reused stale UI XML (FIXED)

**File:** `approach/segment_replay.py`
**Symptom:** After a recovery action changed the screen, the next retry could still label/match elements from the previous UI hierarchy.
**Cause:** `xml_str = device.get_ui_xml()` was captured once before the recovery loop and reused during retries.
**Fix:** Added `parse_live_elements()` and call it on every recovery attempt and before final replay action selection. Applied.

---

### BUG — `input_text` did not focus resolved target field (FIXED)

**File:** `approach/execute_action.py`
**Symptom:** `input_text` typed into whatever field currently had focus, even when replay had resolved a target `position`.
**Cause:** `execute_actions()` ignored `position` for `input_text`.
**Fix:** If an `input_text` action includes `position`, tap that position before sending text. Applied.

---

### PROMPT — Action prompt allowed ambiguous region shape (FIXED)

**File:** `approach/prompts/action_region.py`
**Symptom:** Model could return `region` as a list despite execution expecting one target.
**Cause:** Prompt examples showed a scalar region but did not explicitly forbid lists or explain coordinate fallback.
**Fix:** Prompt now states `region` must be exactly one integer from highlighted regions; otherwise omit `region` and use coordinates/text. Applied.

---

### METRICS — LLM calls/tokens reported as zero despite Gemini calls (FIXED)

**Files:**
- `approach/run_stats.py`
- `approach/providers/gemini_provider.py`
- `approach/providers/openai_provider.py`
- `approach/model_api.py`

**Symptom:** `bad-run-summary.json` showed:
```
"llm_calls": 0,
"tokens_used": 0
```
while logs showed multiple Gemini requests.
**Cause:** Provider calls were not consistently recording response usage/latency into the active run stats tracker.
**Fix:** Added best-effort usage extraction for OpenAI/Gemini response objects and recorded LLM responses in provider calls and ping calls. Applied.

---

### TESTS — Regression coverage added (FIXED)

**Files:**
- `approach/test_segment_replay_contracts.py`
- `approach/test_execute_action.py`

**Coverage:** Region normalization, invalid action rejection, relevant-region normalization, and `input_text` focus-before-typing.
**Verification:**
```
./.venv/bin/python -m pytest approach/test_segment_replay_contracts.py approach/test_execute_action.py approach/test_run_stats.py approach/check_video/test_check_video.py
```
**Result:** `22 passed`.
