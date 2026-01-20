from google import genai
import json
from dotenv import load_dotenv
import os

DIRECTOR_SYSTEM_PROMPT = """
You are an expert Video Editor AI. Your goal is to translate a high-level user request (e.g., "Make it cinematic", "Make it fast-paced") into a specific list of tool execution commands.
Note 1: All these things are of Inshot App so please take care of it while deciding the look and feel of the video
Note 2: If you do not manually set the duration of any image by default it is set to 5 seconds so please take care of that

### AVAILABLE TOOLS
# 1. apply_effect(image_idx: int, effects_list: list[str])
    - Applies one or more effects to image_idx (1-indexed).
    - You can stack up to 2 effects.
    - Example: {{"tool": "apply_effect", "args": {{"image_idx": 1, "effects_list": ["Slow Zoom", "Darken"]}} }}    - applies effect for the whole duration of image1_idx (1-indexed)
        "Slow Zoom": "Basic",
        "Zoom Out": "Basic",
        "Tremble": "Basic",
        "Thrill": "Basic",
        "Roll": "Basic",

        "Glitch": "Glitch",
        "Noise": "Glitch",
        "RGB": "Glitch",

        "Strobe": "Vibrate",
        "Flash": "Vibrate",
        "Flow": "Vibrate",
        "Flicker": "Vibrate",
        "Flip": "Vibrate",
        "Leap": "Vibrate",

        "Node": "Shake",
        "Flutter": "Shake",
        "Bass": "Shake",
        "Shake": "Shake",
        "Cam Shake": "Shake",

        "White": "Fade",
        "Black": "Fade",
        "Mosiac": "Fade",

        "Focus": "Film",
        "Zoom": "Film",
        "Darken": "Film",

        "REC": "Retro",
        "VHS": "Retro",

        "Circle": "Blur",
        "Diamond": "Blur",
        
        "Date": "Analog",
        "Shorts": "Analog",
        "Split": "Analog",

        "Two": "Split",
        "Four": "Split",
        "Nine": "Split",

        "Shatter": "Glass",
        "Shard": "Glass"

    - The key in this json is the name of the effect and the value is the category the effect falls under use this information wisely while selecting the effect
    - in the function argument only provide the key like "Zoom", "Focus" not the value of the key.

2. add_transition(image1_idx: int, image2_idx: int, transition_type: str, all_apply: bool)
   - Applies tranistions between image1_idx and image2_idx (1-indexed)
   - Avaliable transitions
    "none"
    "mix"
    "fade"
    "blur"
    "circlefade"
    "wipe right"
    "wipe left"
    "wipe down"
    "wipe up"
    "slide right"
    "slide left"
    "slide down"
    "slide up"
   - 'all_apply=True' puts the same transition between ALL clips.

4. change_duration(image_idx: int, duration: float)
   - Use this to control for how long the images would be there in the video, controls pacing
   - Note You cannot set the duration of any image below 1.5 seconds

### NOTE
- Images are presented in sequential order first one is 1st image and so on. Furthermore the first image is named image1 and so on
   
### CONSTRAINTS
- You have {num_clips} clips available (Indices 1 to {num_clips}).
- Do NOT hallucinate tools not listed above.
- Output strictly valid JSON.
- Always set the clip duration at the start and then add effects and then add transitions

### OUTPUT FORMAT
{{
  "thought_process": "Brief explanation of your editing choices.",
  "plan": [
      {{ "tool": "tool_name", "args": {{ "arg1": "value", "arg2": "value" }} }}
  ]
}}
"""

class VideoDirector:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client()
        self.model = "gemini-2.5-pro"
        
    def generate_plan(self, user_prompt: str, clips_path: list[str]):
        """
        Translates user_prompt into a JSON execution plan.
        """
        num_clips = len(clips_path)
        # 1. Hydrate the system prompt with current state (num_clips)
        system_instruction = DIRECTOR_SYSTEM_PROMPT.format(num_clips=num_clips)
        
        full_prompt = f"""
        {system_instruction}
        
        USER REQUEST: "{user_prompt}"
        """

        files = []
        for i, path in enumerate(clips_path):
            files.append(self.client.files.upload(file=path, config={
                "display_name": f"image{i}"
            }))

        contents = [full_prompt]
        contents.append("Here is the visual context for the video clips, in order:")

        # Loop to add: "Clip 1" -> [Image Object] -> "Clip 2" -> [Image Object]
        for i, file_obj in enumerate(files):
            contents.append(f"\n--- IMAGE {i+1} ---")
            contents.append(file_obj)
        
        # 2. Call LLM
        print(f"🎬 Director thinking about: '{user_prompt}'...")
        response = self.client.models.generate_content(model=self.model, 
                                                       contents=contents
                                                       )

        print(response.usage_metadata)
        
        # 3. Clean & Parse JSON
        try:
            # Strip markdown code blocks if present
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            plan_data = json.loads(clean_text)
            with open("plan.json", "w") as f:
                json.dump(plan_data, f, indent=4)
            return plan_data
        except Exception as e:
            print(f"❌ Error parsing Director plan: {e}")
            return None

if __name__ == "__main__":
    director = VideoDirector()
    files = os.listdir("images")
    paths = [os.path.join("images", file) for file in files]
    print(director.generate_plan("Somehow make an intresting looking edit from these images", paths))