import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import shutil
import threading
import time
from PIL import Image  # Requires: pip install Pillow
from director import VideoDirector
from agents_functions import select_images, edit_image
import asyncio

# --- Configuration ---
REMOTE_ALBUM_PATH = "/sdcard/Pictures/droidrun"
LOCAL_SYNC_DIR = "images"  # Folder where we rename copies to image1.png, etc.

# --- Backend: ADB Operations --

def format_plan_to_text(plan_json):
    """Converts the Director's JSON into a readable script for the GUI."""
    if not plan_json: return "No plan generated."
    
    output = []
    
    # 1. Thought Process
    thoughts = plan_json.get("thought_process", "No thoughts provided.")
    output.append(f"The Plan:\n{thoughts}\n")
    output.append("-" * 40 + "\n")
    output.append("EXECUTION STEPS:\n")
    
    # 2. Steps
    steps = plan_json.get("plan", [])
    for i, step in enumerate(steps, 1):
        tool = step.get("tool")
        args = step.get("args", {})
        
        # Format specific tools into human-readable text
        if tool == "change_duration":
            line = f"{i}. Set Clip {args.get('image_idx')} duration to {args.get('duration')}s"
        elif tool == "apply_effect":
            effects = ", ".join(args.get('effects_list', []))
            line = f"{i}. Add '{effects}' to Clip {args.get('image_idx')}"
        elif tool == "add_transition":
            t_type = args.get("transition_type")
            all_apply = " (All Clips)" if args.get("all_apply") else ""
            line = f"{i}. Apply '{t_type}' transition{all_apply}"
        elif tool == "add_background_music":
             line = f"{i}. Add Music: {args.get('filename')}"
        else:
            line = f"{i}. {tool}: {args}"
            
        output.append(line)
        
    return "\n".join(output)

def run_adb_command(cmd_list):
    """Run system ADB commands safely."""
    try:
        full_cmd = ["adb"] + cmd_list
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(
            full_cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            startupinfo=startupinfo
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except FileNotFoundError:
         return False, "ADB not found. Install Android SDK platform-tools."

def check_device_connection():
    success, output = run_adb_command(["devices"])
    if not success: return False, output
    devices = [line for line in output.split('\n') if line.strip() and "List of devices" not in line]
    if not devices:
        return False, "No device found. Enable USB Debugging."
    return True, f"Connected: {devices[0].split()[0]}"

def process_files(local_files, status_callback):
    """
    1. Cleans Phone Folder
    2. Pushes New Files
    3. Cleans Local 'images/' Folder
    4. Copies & Renames files locally to image1.png, image2.png...
    """
    total = len(local_files)
    
    # --- STEP 1: PREPARE PHONE ---
    status_callback("Cleaning phone gallery...", 0)
    run_adb_command(["shell", "rm", "-rf", REMOTE_ALBUM_PATH])
    run_adb_command(["shell", "mkdir", "-p", REMOTE_ALBUM_PATH])

    # --- STEP 2: PREPARE LOCAL FOLDER ---
    status_callback("Preparing local sync folder...", 10)
    if os.path.exists(LOCAL_SYNC_DIR):
        shutil.rmtree(LOCAL_SYNC_DIR)
    os.makedirs(LOCAL_SYNC_DIR)

    num_files = len(local_files)

    # --- STEP 3: TRANSFER & SYNC ---
    for i, file_path in enumerate(local_files):
        # A. Push to Phone
        filename = os.path.basename(file_path)
        remote_path = os.path.join(REMOTE_ALBUM_PATH, filename).replace("\\", "/")
        
        progress = 10 + int((i / total) * 80)
        status_callback(f"Processing ({i+1}/{total}): {filename}...", progress)
        
        success, err = run_adb_command(["push", file_path, remote_path])

        timestamp = f"20250101.1200{i:02d}" # 12:00:00, 12:00:01, etc.
        run_adb_command(["shell", "touch", "-t", timestamp, remote_path])
        if not success:
            status_callback(f"Upload Failed: {err}", 0, is_error=True)
            return

        try:
            dest_name = f"image{i+1}.png"
            dest_path = os.path.join(LOCAL_SYNC_DIR, dest_name)
            
            with Image.open(file_path) as img:
                img.save(dest_path, "PNG")
        except Exception as e:
            print(f"Warning: Local conversion failed: {e}")

        # C. Broadcast to Android Gallery
        run_adb_command([
            "shell", "am", "broadcast", 
            "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", 
            "-d", f"file://{remote_path}"
        ])

    status_callback("✅ Ready! Files synced to phone & local folder.", 100, is_success=True)

# --- Frontend: Modern GUI ---
STAGES = ["1.Planning", "2.Setup", "3.Editing"]

class DirectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DroidRun Director Studio")
        self.root.geometry("700x750") # Taller window for the plan view
        
        self.selected_files = []
        self.is_upload_complete = False
        
        # Styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Stage.TLabel", font=("Segoe UI", 9), foreground="#888")
        style.configure("ActiveStage.TLabel", font=("Segoe UI", 10, "bold"), foreground="#4CAF50")

        # --- HEADER ---
        self.conn_frame = tk.Frame(root, bg="#f0f0f0", pady=5)
        self.conn_frame.pack(fill=tk.X)
        self.lbl_conn = tk.Label(self.conn_frame, text="Checking ADB...", bg="#f0f0f0", fg="grey")
        self.lbl_conn.pack()

        # --- STEP 1: INGEST ---
        self.frame_ingest = ttk.LabelFrame(root, text="Step 1: Ingest Footage", padding=10)
        self.frame_ingest.pack(fill=tk.X, padx=10, pady=5)

        self.btn_select = ttk.Button(self.frame_ingest, text="📂 Select Images", command=self.select_images)
        self.btn_select.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.btn_upload = ttk.Button(self.frame_ingest, text="⬆️ Upload & Sync", command=self.start_upload_thread, state=tk.DISABLED)
        self.btn_upload.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # --- STEP 2: DIRECT ---
        self.frame_direct = ttk.LabelFrame(root, text="Step 2: Direct AI", padding=10)
        self.frame_direct.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.txt_prompt = tk.Text(self.frame_direct, height=3, font=("Segoe UI", 10))
        self.txt_prompt.pack(fill=tk.X, pady=5)
        self.txt_prompt.insert("1.0", "Make a cool edit from these images")

        self.btn_run = ttk.Button(self.frame_direct, text="🎬 MAKE EDIT", command=self.start_agent_thread, state=tk.DISABLED)
        self.btn_run.pack(fill=tk.X, pady=5)

        # --- LIVE DASHBOARD (NEW) ---
        self.frame_dash = ttk.LabelFrame(root, text="Live Agent Status", padding=10)
        self.frame_dash.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # A. Stage Tracker
        self.stage_frame = ttk.Frame(self.frame_dash)
        self.stage_frame.pack(fill=tk.X, pady=5)
        self.stage_labels = []
        
        for stage in STAGES:
            lbl = ttk.Label(self.stage_frame, text=stage, style="Stage.TLabel")
            lbl.pack(side=tk.LEFT, expand=True)
            self.stage_labels.append(lbl)

        # B. Plan Viewer
        ttk.Label(self.frame_dash, text="Current Plan & Logs:").pack(anchor="w")
        self.txt_plan = tk.Text(self.frame_dash, height=15, font=("Consolas", 9), bg="#1e1e1e", fg="#00ff00")
        self.txt_plan.pack(fill=tk.BOTH, expand=True)
        self.txt_plan.insert("1.0", "Waiting for command...")

        # Start Checks
        self.check_connection_loop()

    # ... (Keep check_connection_loop, select_images, start_upload_thread, on_upload_update same as before) ...
    # [Rest of code omitted for brevity - copy from previous 'app.py' if needed]
    # IMPORTANT: Update 'start_agent_thread' to pass the update_dashboard callback

    def check_connection_loop(self):
        # ... (Same as previous code)
        is_connected, msg = check_device_connection()
        if is_connected and not hasattr(self, 'mirror_launched'):
            self.launch_scrcpy()
            self.mirror_launched = True
        self.lbl_conn.config(text=f"✅ {msg}" if is_connected else f"❌ {msg}", fg="green" if is_connected else "red")
        self.btn_select.state(['!disabled'] if is_connected else ['disabled'])
        self.root.after(5000, self.check_connection_loop)
    
    def launch_scrcpy(self):
        """
        Launches the scrcpy mirror window.
        Assumes scrcpy.exe is in a folder named 'scrcpy' inside your project.
        """
        scrcpy_path = os.path.join("scrcpy", "scrcpy.exe")
        
        # Check if we have the tool
        if not os.path.exists(scrcpy_path):
            print("⚠️ scrcpy not found. Skipping mirror.")
            # Fallback: Maybe they installed it globally?
            scrcpy_path = "scrcpy" 

        try:
            print("📱 Launching Screen Mirror...")
            # --always-on-top: Keeps it visible while you use the GUI
            # --window-x/y: Positions it (optional, remove if it bugs out)
            # --max-size: Limits resolution for faster performance (e.g. 1024)
            subprocess.Popen(
                [scrcpy_path, "--always-on-top", "--window-title=Samsung View", "--max-size=1024"],
                creationflags=subprocess.CREATE_NO_WINDOW # Hide console on Windows
            )
        except Exception as e:
            print(f"Failed to launch scrcpy: {e}")

    def select_images(self):
        # ... (Same as previous code)
        files = filedialog.askopenfilenames(filetypes=(("Images", "*.jpg *.png"), ("All", "*.*")))
        if files:
            self.selected_files = files
            self.btn_upload.state(['!disabled'])

    def start_upload_thread(self):
        # ... (Same as previous code)
        self.btn_upload.state(['disabled'])
        threading.Thread(target=process_files, args=(self.selected_files, self.on_upload_update), daemon=True).start()

    def on_upload_update(self, msg, progress_val, is_error=False, is_success=False):
        # ... (Same as previous code)
        if is_success:
             self.is_upload_complete = True
             self.btn_run.state(['!disabled'])
             messagebox.showinfo("Ready", "Files synced.")

    def start_agent_thread(self):
        prompt = self.txt_prompt.get("1.0", tk.END).strip()
        self.btn_run.state(['disabled'])
        self.update_dashboard("status", "Initializing...")
        
        # Pass the 'update_dashboard' method to the thread
        threading.Thread(target=run_agent_workflow, args=(prompt, self.update_dashboard), daemon=True).start()

    def update_dashboard(self, action, data=None):
        """
        Master method to update the GUI from the background thread.
        action: 'stage', 'plan', 'log', 'finish'
        """
        # Ensure thread safety with root.after if needed, but simple config usually works
        
        if action == "stage":
            # Highlight the active stage
            active_idx = data # 0 to 3
            for i, lbl in enumerate(self.stage_labels):
                if i == active_idx:
                    lbl.configure(style="ActiveStage.TLabel")
                else:
                    lbl.configure(style="Stage.TLabel")
        
        elif action == "plan":
            # Pretty print the JSON
            formatted_text = format_plan_to_text(data)
            self.txt_plan.delete("1.0", tk.END)
            self.txt_plan.insert("1.0", formatted_text)
            
        elif action == "log":
            # Append log message
            self.txt_plan.insert(tk.END, f"\n> {data}")
            self.txt_plan.see(tk.END)
            
        elif action == "finish":
            self.btn_run.state(['!disabled'])
            messagebox.showinfo("Done", data)


def run_agent_workflow(user_prompt, ui_callback):
    """
    Runs the full pipeline and updates the GUI at each step.
    ui_callback(action, data)
    """
    try:
        # --- STAGE 1: PLANNING ---
        ui_callback("stage", 0) # Highlight "Planning"
        ui_callback("log", f"🤖 Agent started. Analyzing prompt: '{user_prompt}'...")
        
        director = VideoDirector()
        files = os.listdir("images")
        paths = [os.path.join("images", file) for file in files]
        plan = director.generate_plan(user_prompt, paths)
        print(plan)

        ui_callback("plan", plan) 
        
        # --- STAGE 2: SETUP ---
        ui_callback("stage", 1) # Highlight "Setup"
        ui_callback("log", "📂 Opening InShot and importing media...")
        
        asyncio.run(select_images())

        ui_callback("stage", 2) # Highlight "Setup"
        ui_callback("log", "Editing")

        asyncio.run(edit_image(len(files), plan["plan"]))
        
    except Exception as e:
        print(f"Agent Error: {e}")
        ui_callback("log", f"❌ ERROR: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DirectorApp(root)
    root.mainloop()