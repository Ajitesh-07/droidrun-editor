import asyncio
from droidrun import DroidAgent, DroidrunConfig, LLMProfile, LoggingConfig, AgentConfig, TracingConfig, CodeActConfig, ManagerConfig, ExecutorConfig, Tools
from dotenv import load_dotenv
from phoenix.otel import register
from tools.inshot_tools import InshotTools
from pydantic import BaseModel, Field

async def select_images_tool(tools: Tools, **kwargs):
    ui_state = (await tools.get_state())[2]

    id = -1
    start = False
    elems = []
    for elem in ui_state:
        if elem.get("resourceId", "") == "com.camerasideas.instashot:id/wallRecyclerView":
            id = elem.get("index", "")
            start = True
            continue

        if not start: continue

        id_now = elem.get("index", "")
        if id_now - id > 1:
            if elem.get("resourceId") == "":
                elems.append(elem)
            else:
                start = False

    print(elems)
    print(len(elems))
    
    for elem in elems:
        try:
            bounds_str = elem.get("bounds", "0,0,0,0")
            bounds = [int(x) for x in bounds_str.split(',')]
            center_x = (bounds[0] + bounds[2]) // 2
            center_y = (bounds[1] + bounds[3]) // 2
            
            print(f"👇 Tapping Image at ({center_x}, {center_y})")
            InshotTools._adb_tap(center_x, center_y)
            
        except Exception as e:
            print(f"❌ Failed to tap element: {e}")

    id = InshotTools._find_node_by_id(tools, "com.camerasideas.instashot:id/applySelectVideo")
    await tools.tap_on_index(id)
    print("✅ Selection Complete")

def getProfile():
    """Get default agent specific LLM profiles."""
    return {
        "manager": LLMProfile(
            provider="GoogleGenAI",
            model="models/gemini-2.5-flash",
            temperature=0.2,
            kwargs={},
        ),
        "executor": LLMProfile(
            provider="GoogleGenAI",
            model="models/gemini-2.5-flash",
            temperature=0.1,
            kwargs={},
        ),
        "codeact": LLMProfile(
            provider="GoogleGenAI",
            model="models/gemini-2.5-flash",
            temperature=0.2,
            kwargs={},
        ),
        "text_manipulator": LLMProfile(
            provider="GoogleGenAI",
            model="models/gemini-2.5-flash",
            temperature=0.3,
            kwargs={},
        ),
        "app_opener": LLMProfile(
            provider="GoogleGenAI",
            model="models/gemini-2.5-flash",
            temperature=0.0,
            kwargs={},
        ),
        "scripter": LLMProfile(
            provider="GoogleGenAI",
            model="models/gemini-2.5-flash",
            temperature=0.1,
            kwargs={},
        ),
        "structured_output": LLMProfile(
            provider="GoogleGenAI",
            model="models/gemini-2.5-flash",
            temperature=0.0,
            kwargs={},
        ),
    }

def getAgentConfig(reasoning = False, vision=False):
    return AgentConfig(
        reasoning=reasoning,
        codeact=CodeActConfig(vision=vision, execution_timeout=10000),
        manager=ManagerConfig(vision=vision),
        executor=ExecutorConfig(vision=vision)
    )

async def select_images():
    goal = """
            Open inshot app and select all the images from the droidrun_images and go the video editor screen and your job is done.
            Note this instruction while finding the droidrun_images folder if u dont see it directly 
            - **CRITICAL: Finding the Folder**
            - The folder list is sensitive.
            - To scroll down, use **TINY SWIPES**.
            - **Instruction:** Swipe from (540, 1500) to (540, 1100). NEVER swipe more than 400 pixels at a time.
            - If you don't see it, swipe again (small swipe).
            - Note for selecting images STRICTLY CALL select images tool call
            
            **CRITICAL: DO NOT CLICK ON THE BLANK IMAGE AT THE VERY START OF THE IMAGE SELECTION SCREEN IGNORE IT AND SELECT EVERYTHING*
            **CRITICAL: FOR SELECTING IMAGES STRICTLY USE THE select images tool call
        """
    
    custom_tools = {
        "select_images": {
            "arguments": [],
            "description": "Selects the images",
            "function": select_images_tool
        }
    }
    
    load_dotenv()
    tracer_provider = register(
        project_name="droidrun-video-editor", 
        endpoint="http://127.0.0.1:6006/v1/traces",
        auto_instrument=True  # Automatically hooks into HTTP/LLM calls
    )
    
    # 1. Setup the config to force the cheaper Flash model
    config = DroidrunConfig(
        agent=getAgentConfig(reasoning=False, vision=True),
        llm_profiles=getProfile(),
        logging=LoggingConfig(debug=True, save_trajectory="action"),
        tracing=TracingConfig(enabled=True, provider="phoenix")
    )

    agent = DroidAgent(
        goal=goal,
        config=config,
        custom_tools=custom_tools
    )

    result = await agent.run()

    return result.success

    

import json # Ensure json is imported

async def edit_image(num_images, plan):
    load_dotenv()
    tracer_provider = register(
        project_name="droidrun-video-editor", 
        endpoint="http://127.0.0.1:6006/v1/traces",
        auto_instrument=True 
    )
    
    config = DroidrunConfig(
        agent=getAgentConfig(reasoning=False, vision=True),
        llm_profiles=getProfile(),
        logging=LoggingConfig(debug=True, save_trajectory="none"),
        tracing=TracingConfig(enabled=True, provider="phoenix")
    )

    print(f"🃏 App Cards Enabled: {config.agent.app_cards.enabled}")
    
    # 1. Convert plan dict to a pretty string for the prompt
    plan_str = json.dumps(plan, indent=4)

    # 2. Inject num_images and plan into the goal
    goal = f"""
        Phase 1: Setup & Physics
        - Call 'calibrate(num_images={num_images})' to map the timeline.

        Phase 2: Execution
        Follow this execution plan strictly. Convert the JSON below into tool calls. 
        Try to call multiple tools in one go (parallel execution) where possible for speed.

        EXECUTION PLAN:
        {plan_str}
        """

    custom_tools = {
        "calibrate": {
            "arguments": ["num_images"],
            "description": "CRITICAL FIRST STEP. Measures the timeline scale (pixels per second). usage: calibrate(num_images=4)",
            "function": InshotTools.calibrate
        },
        "seek_timeline": {
            "arguments": ["time"],
            "description":  "Moves the playhead to a specific timestamp in seconds (e.g. 12.5). Automatically corrects position if it misses.",
            "function": InshotTools.seek_timeline
        },
        "add_transition": {
            "arguments": ["image1_idx", "image2_idx", "transition_type", "all_apply"],
            "description": "Adds a transition between two images. image1_idx/image2_idx are 1-based. all_apply=True applies to ALL clips (use idx 1 & 2 as placeholders).",
            "function": InshotTools.add_transition
        },
        "change_duration": {
            "arguments": ["image_idx", "duration"],
            "description": "Changes the duration of a specific clip. image_idx is 1-based. duration is in seconds.",
            "function": InshotTools.change_duration
        },
        "apply_effect": {
            "arguments": ["image_idx", "effects_list"],
            "description": "Applies a list of visual effects to a specific clip. image_idx is 1-based. effects_list is a list of strings (e.g. ['Slow Zoom', 'Darken']). Max 2 effects.",
            "function": InshotTools.apply_effect
        }
    }

    # 3. Define your goal
    agent = DroidAgent(
        goal=goal,
        config=config,
        custom_tools=custom_tools
    )

    # 4. Run it
    result = await agent.run()

    return result

if __name__ == "__main__":
    with open("plan.json", "r") as f:
        plan = json.load(f)
    asyncio.run(edit_image(4, plan["plan"]))