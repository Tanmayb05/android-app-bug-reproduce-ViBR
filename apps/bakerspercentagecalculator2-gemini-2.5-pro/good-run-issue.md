# Run Issue: Coordinate-Based Action Execution Failure

**App:** bakerspercentagecalculator2  
**Model:** gemini-2.5-pro  
**Video Quality:** good  
**Status:** INCOMPLETE (0/3 segments executed)

## Issue Summary

LLM generated tap actions using hardcoded pixel coordinates instead of element-based selectors. Coordinates were valid in the reference video but stale in the live device state, causing taps to miss or hit unintended elements. This resulted in catastrophic state divergence (recipe list → empty state) and cascading action failures across all segments.

## Root Cause

**Action Resolution Pipeline Issue:**

The `resolve_action_position()` function in `segment_replay.py` attempts to map LLM actions to device elements in this order:

1. **Region index** → DINO detection bounding box center
2. **Text match** → Search XML elements by text content
3. **Position fallback** → Find closest element to hardcoded coordinates

**Problem:** The LLM action format (defined in `prompts/action_region.py`) only supports:
- `"region"`: integer index into highlighted DINO regions
- `"position"`: raw pixel coordinates [x, y]
- No `"text"` field option

When LLM returns `"position"` (which it does when no relevant DINO region is highlighted), the code attempts text-based matching first (which always fails since no text field exists), then falls back to **coordinate-based closest-element matching**. This fails when:

1. Coordinates derive from the reference/start image, not the live device
2. Device has different screen resolution/DPI than source video
3. UI elements are not visible in live state (e.g., menu already closed, different activity)

## Evidence

**Log traces (lines 140-160 of good-run.log):**

```
[execute_action] [1] Tap the three dots icon in the top right corner. -> tap
Recovery matched element: '' at (540, 147)
```

Repeated 3 times with identical coordinate (540, 147), suggesting:
- Fallback to position-based closest-element matching
- Element text is empty (`''`), indicating stale/wrong element
- No element in XML actually matches the intended 3-dots menu icon

**Visual evidence (screenshot comparison):**

- `step_0v_tmp_start.png`: Recipe "cake" visible + menu open in background
- `step_0e_screenshot_1.png` (after tap): Empty state "Press the + button to add your first recipe"

**Conclusion:** Tap at (540, 147) either:
1. Navigated away from current activity (hit back/menu close)
2. Hit unintended element (e.g., overlay dismissal button)
3. Missed entirely due to coordinate mismatch between reference and device

## Impact

- **Segment 0:** 3 failed recovery attempts → action skipped → state misalignment
- **Segment 1:** Similar 3-dots tap failures due to corrupted state from Segment 0
- **Segment 2:** Different action type (tap '+' button) succeeded, but baseline already broken
- **Overall:** 0/3 segments completed; 25 LLM calls wasted on recovery loops

## Recommended Fixes

### Priority 1: Extend LLM Action Format
Add `"text"` field to action format in `prompts/action_region.py`:

```json
{
  "action": "tap",
  "text": "three dots icon",
  "description": "Tap the three-dot menu icon to open options."
}
```

Update `match_action_to_element()` to search by text description + fuzzy matching against XML content and accessibility labels.

### Priority 2: Use DINO Region Matching
Force LLM to always return `"region"` index when available (modify prompt to highlight 3-dots as region 9). Avoid coordinate fallback entirely for critical UI elements.

### Priority 3: Validate Coordinates
Before executing tap, check if element at coordinate(s) actually exists in live XML. If not found, re-query LLM for text-based description or region index.

### Priority 4: Add State Validation
After each action, compare reference stop state vs live state using LLM vision. If mismatch > threshold, trigger recovery before proceeding to next segment.

## Metadata

- **Segments:** 4 total (0, 1, 2, 3 skipped)
- **LLM Calls:** 25 (10 action decisions, 15 recovery/consistency checks)
- **Total Latency:** 304.84s
- **Cost:** $0.0439
- **Video Frames:** 211
- **Clip Similarity Cache:** Hit (reused from prior run)