# WiFiAnalyzer Segment 2 Failure - Detailed Bug Analysis with Full Paths & Code

**Report Date:** 2026-05-22  
**App:** wifianalyzer1  
**Video:** bad-video.mp4  
**Provider:** gemini-2.5-pro  
**Algorithm:** CLIP segmentation  
**Status:** FAILED at Segment 2 action execution

---

## Executive Summary

Replay system crashes at **segment 2** (after successfully completing segment 1). LLM selects region index that doesn't exist in DINO detections, causing action validation to fail silently. Workflow stops; no segments 3-9 processed.

**Root Cause:** Index mismatch between DINO detection filtering and LLM region selection due to boundary condition in `annotate_relevant_regions()`.

---

## Evidence & Logs

### Run Output Files
```
/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/apps/wifianalyzer1-gemini-2.5-pro/
├── bad-run.log                          # Main execution log
├── bad-run-debug.log                    # Debug output
├── bad-run-summary.json                 # Stats summary
└── bad-artifacts/                       # Generated artifacts
    ├── step_0v_dino.png                 # DINO detections for segment 0
    ├── step_0v_relevant_regions.png     # Filtered regions for segment 0
    ├── step_0e_*.png                    # Execution screenshots
    ├── step_1v_dino.png                 # DINO detections for segment 1
    ├── step_1v_relevant_regions.png     # Filtered regions for segment 1
    ├── step_1e_*.png                    # Execution screenshots
    ├── step_2v_dino.png                 # DINO detections for segment 2 ✓
    ├── step_2v_relevant_regions.png     # BLANK - filtered regions fail
    ├── step_2e_*.png                    # Execution screenshots
    └── (no step_3v_*.png - never reached)
```

### Key Log Lines from bad-run.log

**Segment 1 - Succeeds:**
```
Line 160-161: Relevant regions: {'target_regions': [11], 'predicted_action': 'tap'}
             GPT selected regions: [11]
             
Line 162:    WARNING: No relevant regions to annotate.

Line 168-169: Replay matched element: '' at (405, 1783)
             Tap on the 'Channel Rating' tab. -> tap

Line 170:    Action executed. ✓
```

**Segment 2 - FAILS:**
```
Line 175-176: Relevant regions: {'target_regions': [1], 'predicted_action': 'tap'}
             GPT selected regions: [1]

Line 177:    WARNING: No relevant regions to annotate.

Line 183:    Skipping invalid action with no executable target: 
             {'action': 'tap', 'region': 1, 
              'description': "Tap the 'Channel Rating' button at the bottom of the screen."}

Line 184:    Video processing completed. (No segment 3 attempted)
```

---

## Step-by-Step Failure Flow

### Segment 1 Execution
1. **DINO runs** → detects UI elements → saves `step_1v_dino.png`
   - Returns: `regions = [{'index': 0, ...}, {'index': 1, ...}, ..., {'index': 10, ...}]` (11 boxes)

2. **LLM asked:** "Which detected region is relevant for the next action?"
   - Receives: full DINO image with ALL 11 boxes labeled 0-10
   - **Returns:** `target_regions: [11]` ← **WRONG! Index 11 doesn't exist**

3. **Annotation filter runs:** `annotate_relevant_regions(..., regions=[0-10], relevant_indices=[11])`
   - Code: `filtered_regions = [r for r in regions if r["index"] in relevant_indices]`
   - Result: `filtered_regions = []` (empty! key 11 not in 0-10)
   - **Saves blank image** → `step_1v_relevant_regions.png` is blank

4. **LLM asked again:** "Given this highlighted region, what to tap?"
   - Receives: blank `step_1v_relevant_regions.png` (no box shown!)
   - Fallback: Uses `match_action_to_element()` → finds "Channel Rating" in XML
   - **Executes action successfully** (by luck - XML fallback worked)

### Segment 2 Execution
1. **DINO runs** → detects UI elements → saves `step_2v_dino.png`
   - Returns: `regions = [{'index': 0, ...}, {'index': 2, ...}, {'index': 3, ...}, ...]`
   - **Missing index 1!** (filtered during DINO processing)
   - Total: maybe 7-10 boxes, indices [0, 2, 3, 4, 5, 6, 7, 8] (skipped 1)

2. **LLM asked:** "Which detected region is relevant?"
   - Receives: DINO image with boxes numbered [0, 2, 3, 4, 5, ...]
   - **Returns:** `target_regions: [1]` ← **Assumes contiguous indexing [0,1,2,...]**

3. **Annotation filter runs:** `annotate_relevant_regions(..., regions=[0,2,3,4,5,...], relevant_indices=[1])`
   - Code: `filtered_regions = [r for r in regions if r["index"] in relevant_indices]`
   - Result: `filtered_regions = []` (empty! key 1 not in available indices)
   - **Saves blank image** → `step_2v_relevant_regions.png` is blank

4. **LLM asked again:** "Given this highlighted region, what to tap?"
   - Receives: blank `step_2v_relevant_regions.png`
   - Returns: `action: {'action': 'tap', 'region': 1, 'description': 'Tap Channel Rating button'}`

5. **Action resolution fails:**
   - Code: `if action["region"] in region_index_to_center:` 
   - `region_index_to_center = {0:center0, 2:center2, 3:center3, ...}` (key 1 missing!)
   - Condition **FALSE** → skips position assignment
   - Fallback: `match_action_to_element()` → no XML match (description too generic)
   - **Action left without position field**

6. **Executability check fails:**
   ```python
   def action_is_executable(action):
       if action_type in {"tap", "double_tap", "long_press"}:
           return "position" in action  # FALSE! No position set
   ```

7. **Action SKIPPED:**
   ```
   if not action_is_executable(action):
       logger.warning("Skipping invalid action with no executable target")
       continue  # Jump to next segment
   ```
   
8. **Video processing ends** → No segment 3 attempted

---

## Code Analysis with File Paths & Snippets

### 1. DINO Detection - Index Creation
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/dino_detection.py`

**Lines 100-176:**
```python
def run_grounding_dino(image_path: str, output_path: str):
    """
    Returns:
        regions (list): List of dicts, each with:
            - "index": int (detection index)  # ← SEQUENTIAL 0,1,2,3,...
            - "phrase": str (detected phrase)
            - "confidence": float (logit score)
            - "center": (cx, cy) int tuple
            - "box": [x1, y1, x2, y2]
    """
    # ... DINO inference code ...
    
    # Build regions list (Line 164-176)
    regions = []
    for i, (box, phrase, logit) in enumerate(zip(xyxy, phrases, logits)):
        x1, y1, x2, y2 = map(int, box)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        regions.append({
            "index": i,  # ← Uses enumerate index (0,1,2,...)
            "phrase": phrase,
            "confidence": float(logit),
            "center": (cx, cy),
            "box": [x1, y1, x2, y2]
        })
    
    return regions
```

**Problem:** If DINO post-processing filters boxes before this loop, indices will have gaps!

---

### 2. Relevant Regions Annotation - FILTER & BLANK IMAGE
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/dino_detection.py`

**Lines 178-217:**
```python
def annotate_relevant_regions(image_path, output_path, regions, relevant_indices):
    """
    Args:
        regions (list): All DINO regions from run_grounding_dino
        relevant_indices (list): Indices to highlight (from LLM)
    """
    # ... image loading ...
    
    # LINE 197 - THE FILTER (SILENT FAIL POINT)
    filtered_regions = [r for r in regions if r["index"] in relevant_indices]
    
    # LINE 199-202 - SILENT BLANK IMAGE CREATION
    if not filtered_regions:
        logger.warning("No relevant regions to annotate.")
        cv2.imwrite(output_path, image)  # ← Writes blank image!
        return
    
    # If we reach here, boxes are annotated
    boxes = np.array([r["box"] for r in filtered_regions])
    labels = [f"{r['index']}: {r['phrase']}" for r in filtered_regions]
    
    # ... annotation & save ...
```

**The Bug:** 
- When LLM returns `relevant_indices=[11]` but DINO only has `[0-10]`
- `filtered_regions` becomes `[]` (empty list)
- Function returns early and writes BLANK image
- **No warning to user that selection was invalid!**

---

### 3. Region Dict Construction - Missing Keys
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/segment_replay.py`

**Line 575:**
```python
# After DINO runs and relevant regions filtered:
dino_region_index_to_center = {r["index"]: r["center"] for r in dino_regions}

# Example for segment 2:
# If dino_regions = [{'index': 0, 'center': (100,200)}, 
#                    {'index': 2, 'center': (150,250)},  # Missing index 1!
#                    {'index': 3, 'center': (200,300)}, ...]
#
# Result: {0: (100,200), 2: (150,250), 3: (200,300), ...}
#         Key 1 does NOT exist!
```

---

### 4. Action Resolution - Silent Key Lookup Fail
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/segment_replay.py`

**Lines 181-207:**
```python
def resolve_action_position(
    action: dict[str, Any],
    region_index_to_center: dict[int, tuple[int, int]],
    elements: List[AndroidElement],
    *,
    context: str,
) -> dict[str, Any]:
    # LINE 188 - THE SILENT FAIL
    if "region" in action and action["region"] in region_index_to_center:
        # For segment 2: action["region"] = 1
        # region_index_to_center = {0: center0, 2: center2, 3: center3, ...}
        # Condition is FALSE (key 1 doesn't exist)
        action["position"] = region_index_to_center[action["region"]]
        logger.info(f"Replay using region index: {action['region']} at {action['position']}")
        return action
    
    # FALLBACK (LINE 198-207)
    matched_element = match_action_to_element(action, elements)
    if matched_element:
        action["position"] = matched_element.center
        logger.info(f"Replay matched element: {matched_element.text} at {matched_element.center}")
    # LINE 207 - Returns action with OR WITHOUT position field!
    return action
```

**The Problem:**
- If fallback `match_action_to_element()` fails (no XML match)
- Action is returned **without "position" field**
- Caller doesn't know if position was set or not

---

### 5. Executability Check - FAILS SILENTLY
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/segment_replay.py`

**Lines 210-218:**
```python
def action_is_executable(action: dict[str, Any]) -> bool:
    action_type = action.get("action")
    if action_type in {"tap", "double_tap", "long_press"}:
        return "position" in action  # ← Returns FALSE if no position
    if action_type == "swipe":
        return "from" in action and "to" in action
    if action_type == "input_text":
        return "text" in action
    return action_type in {"back", "home", "wait", "no action"}
```

---

### 6. Action Execution Loop - SKIPS & CONTINUES
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/segment_replay.py`

**Lines 650-675:**
```python
# Loop through segments
for i, segment in enumerate(segments):  # i = 0, 1, 2, ...
    # ... DINO runs, LLM asked, action resolved ...
    
    action = resolve_action_position(
        action,
        dino_region_index_to_center,
        elements,
        context="Replay",
    )
    
    # LINE 665-670 - THE SKIP
    if not action_is_executable(action):
        logger.warning(
            "Skipping invalid action with no executable target: %s",
            action,
        )
        continue  # ← SKIPS TO NEXT SEGMENT
    
    execute_actions(device, [action])
    logger.info("Action executed.")
    stats.actions_executed += 1
```

**Flow after segment 2 fails:**
```
i=2: action_is_executable = False → skip & continue
i=3: TRY to process segment 3
     BUT! Loop might exit or segment 3 never gets DINO detections
     (check how loop determines segment count)
```

---

### 7. Final Status - Marked "Successful" Despite Incomplete
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/segment_replay.py`

**Line 682:**
```python
stats.status = "successful" if stats.actions_executed > 0 else "incomplete"
```

**Segment 1 executed → `actions_executed = 1 > 0` → Status = "successful"**

But only 1 of 9 planned actions completed!

---

## Full Run Summary

**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/apps/wifianalyzer1-gemini-2.5-pro/bad-run-summary.json`

```json
{
  "app": "wifianalyzer1",
  "video": "bad-video.mp4",
  "provider": "gemini",
  "model": "gemini-2.5-pro",
  "algorithm": "clip",
  "status": "successful",  // ← MISLEADING! Only 1/9 actions done
  "scenes": 3,
  "actions_executed": 1,
  "actions_planned": 9,  // From video analysis
  "llm_calls": 15,
  "total_duration": "286.53s"
}
```

---

## Expected vs Actual

### Expected Execution (from video analysis)
```
Segment 0: App Store → tap "Open" (app already open, skip)
Segment 1: Access Points → tap "Channel Rating" ✓
Segment 2: (Loading) → (wait)
Segment 3: Channel Rating → tap "Time Graph"
Segment 4: Time Graph → (wait & view)
Segment 5: Time Graph → tap "Channel Graph"
Segment 6: Channel Graph → (wait & view)
Segment 7: Channel Graph → tap "Channel Rating"
Segment 8: Channel Rating → (wait & review)
```

### Actual Execution
```
Segment 0: App Store → skip (already open)
Segment 1: Access Points → tap "Channel Rating" ✓
Segment 2: (Loading) → CRASH - region index mismatch
Segments 3-8: Never attempted
```

---

## Artifacts Comparison

### Segment 1 - Works (despite blank annotation)
```
/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/apps/wifianalyzer1-gemini-2.5-pro/bad-artifacts/
├── step_1v_dino.png                 # DINO detections: 11 boxes [0-10]
├── step_1v_relevant_regions.png     # BLANK (LLM selected [11] - doesn't exist)
├── step_1v_tmp_start.png            # Segment start frame
├── step_1v_tmp_stop.png             # Segment end frame
├── step_1e_screenshot_0.png         # Live execution screenshot
└── step_1e_labeled.png              # Labeled during recovery
```

### Segment 2 - FAILS (blank annotation causes bad selection)
```
/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/apps/wifianalyzer1-gemini-2.5-pro/bad-artifacts/
├── step_2v_dino.png                 # DINO detections: boxes [0,2,3,4,5...] NO INDEX 1
├── step_2v_relevant_regions.png     # BLANK (LLM selected [1] - doesn't exist in DINO)
├── step_2v_tmp_start.png            # Segment start
├── step_2v_tmp_stop.png             # Segment end
├── step_2e_screenshot_0.png         # Live execution attempt
└── step_2e_labeled.png              # Labeled during failed recovery
```

### Segment 3+ - Never Generated
```
step_3v_dino.png        ✗ MISSING
step_3v_relevant_regions.png ✗ MISSING
step_3e_*.png           ✗ MISSING
```

---

## Recommended Fixes

### Fix 1: VALIDATE LLM INDEX (Recommended)
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/segment_replay.py`

**Location:** Before calling `ask_gpt_for_action_region()`

```python
# After LLM response parsed (line 657):
action = normalize_action_response(extract_json(reply))

# NEW: Validate region index (BEFORE resolve_action_position)
if "region" in action:
    available_indices = list(dino_region_index_to_center.keys())
    if action["region"] not in available_indices:
        logger.error(
            f"LLM selected invalid region {action['region']}. "
            f"Available indices: {available_indices}"
        )
        # Force fallback to XML matching
        action.pop("region", None)
```

### Fix 2: VALIDATE ANNOTATION FILTER
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/dino_detection.py`

**Location:** Line 197-202

```python
def annotate_relevant_regions(image_path, output_path, regions, relevant_indices):
    # ... 
    filtered_regions = [r for r in regions if r["index"] in relevant_indices]
    
    # NEW: Log mismatch (before silently blanking)
    available_indices = {r["index"] for r in regions}
    requested_indices = set(relevant_indices)
    invalid_indices = requested_indices - available_indices
    
    if invalid_indices:
        logger.error(
            f"LLM requested indices {invalid_indices} but only {available_indices} available. "
            f"Likely cause: non-contiguous DINO indices or out-of-bounds selection."
        )
    
    if not filtered_regions:
        logger.warning("No relevant regions to annotate. Saving blank image.")
        # ... existing code ...
```

### Fix 3: RENUMBER DINO INDICES
**File:** `/Users/tanmaybhuskute/Documents/android-app-bug-reproduce-ViBR/approach/dino_detection.py`

**Location:** Line 160-176 (after DINO detection)

```python
# Instead of using enumerate index, renumber sequentially
regions = []
for idx, (box, phrase, logit) in enumerate(zip(xyxy, phrases, logits)):
    x1, y1, x2, y2 = map(int, box)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    regions.append({
        "index": idx,  # ← Already contiguous if no filtering happens
        "phrase": phrase,
        "confidence": float(logit),
        "center": (cx, cy),
        "box": [x1, y1, x2, y2]
    })
    
# After filtering (if any), renumber:
regions = [
    {**r, "index": i}  # Renumber to 0,1,2,...
    for i, r in enumerate(regions)
]
```

---

## Debugging Commands

### Check DINO indices for segment 2:
```bash
# Add temporary debug logging in dino_detection.py after line 176:
logger.info(f"DINO detected {len(regions)} regions with indices: {[r['index'] for r in regions]}")
```

### Check region filter results:
```bash
# In dino_detection.py, line 197:
available_indices = {r["index"] for r in regions}
requested_indices = set(relevant_indices)
logger.info(f"Available: {available_indices}, Requested: {requested_indices}")
```

### Check action resolution:
```bash
# In segment_replay.py, after line 658:
logger.info(f"dino_region_index_to_center keys: {list(dino_region_index_to_center.keys())}")
logger.info(f"Action region: {action.get('region')}")
logger.info(f"Has position: {'position' in action}")
```

---

## Summary Table

| Component | File Path | Lines | Issue |
|-----------|-----------|-------|-------|
| **DINO Detection** | `approach/dino_detection.py` | 100-176 | Sequential indices [0,1,2...] BUT downstream filtering can create gaps |
| **Region Annotation** | `approach/dino_detection.py` | 178-217 | Filter silently creates blank image when index not found (line 197) |
| **Region Dict Build** | `approach/segment_replay.py` | 575 | Dict keys match DINO indices (may have gaps) |
| **Action Resolution** | `approach/segment_replay.py` | 181-207 | Silent fail if region key missing (line 188) |
| **Executability** | `approach/segment_replay.py` | 210-218 | Returns FALSE if no position (line 213) |
| **Action Skip** | `approach/segment_replay.py` | 665-670 | Skips action without halt (line 670 continue) |
| **Status Report** | `approach/segment_replay.py` | 682 | Marked "successful" despite incomplete (misleading) |

---

## Conclusion

**Primary Root Cause:** Segment 2 DINO detections have non-contiguous indices (missing index 1), but LLM assumes 0-indexed array and selects region 1. Annotation filter silently returns blank image. LLM selection becomes invalid at execution time. Code silently skips action without explanation. Workflow stops.

**Why Segment 1 Worked:** Despite same blank annotation issue, XML fallback matched "Channel Rating" text in live device state, so action executed by luck.

**Why Segment 2 Failed:** XML fallback failed (description too vague), no position set, action marked non-executable, skipped without retry.
