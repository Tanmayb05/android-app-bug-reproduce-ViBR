PROMPT = """
      You are given two screenshots of an Android interface:

      1. The first image is the REFERENCE state before an interaction.
      2. The second image is the FOLLOW-UP state after the interaction.

      You are also given a list of interactive UI regions detected in the reference image. Each region includes:
      - A numeric index
      - A bounding box
      - A phrase describing the region, e.g. button or text field

      Your task is to determine which of these regions are most likely involved in the transition between the two states.

      - Focus on regions that, if interacted with, could explain the visual change between the first and second image.
      - Minor layout shifts or content changes are not enough. Identify only regions that are plausible interaction targets.
      - Use the phrases and bounding boxes to reason about the intent of the user.
      - When pointers or animations on a button or similar can be seen, prioritize the region around it.

      You must also predict the type of user action that caused the change. Choose only from:
      ["tap", "double_tap", "long_press", "swipe", "input_text", "back", "home", "wait", "no action"]

      Respond strictly in this JSON format. If no regions are relevant, return an empty list:
      { "target_regions": [int, int, ...], "predicted_action": "<action>" }
      """
