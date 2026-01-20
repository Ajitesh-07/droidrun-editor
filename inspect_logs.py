from redis_state import global_state

print("🧠 INSPECTING REDIS MEMORY...")

# 1. Check Physics Constant
px = global_state.get("px/sec")
print(f"📏 Pixels Per Second: {px}")

# 2. Check Timeline Map
timeline = global_state.get("timeline_map")
print(f"🗺️ Timeline Map: {timeline}")

# 3. Check Metadata
total = global_state.get("total_video_duration")
print(f"⏱️ Total Duration: {total}")