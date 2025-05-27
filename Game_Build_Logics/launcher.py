import os
import sys
import json
import random
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from urllib.parse import parse_qs, urlparse
import hashlib
import base64

## Attempt to fix XGBoost VERSION file before importing anything else
try:
    from xgboost_VERSION_fix import fix_xgboost_version
    fix_xgboost_version()
except ImportError:
    print("XGBoost VERSION fix module not found")

## Import game components
from game_engine import Game, EmotionSystem
from emotion_systems.random_emotion import RandomEmotionSystem
from emotion_systems.rule_based_emotion import RuleBasedEmotionSystem
from emotion_systems.ml_emotion import MLEmotionSystem

## Constants
DATA_FOLDER = "data"
CONFIG_FILE = "config.json"
COMPLETION_FILE = "completion_status.json"
DEFAULT_TIME_LIMIT = 120  
VERIFICATION_CODE_LENGTH = 6 

## Define class launcher
class LauncherApp:
    def __init__(self, root, admin_mode=False):
        self.root = root
        self.root.title("NPC Emotion Game - Research Study Launcher")
        self.root.geometry("800x650")
        
        ## Track if we're in admin mode for testing
        self.admin_mode = admin_mode
        
        ## Load configuration if it exists
        self.config = self.load_config()
        
        ## Create and place widgets
        self.create_widgets()
        
        ## Check for command line arguments
        self.check_command_line_args()
    
    def clean_url(self, url):
        """Clean URL by removing whitespace and newlines"""
        if url:
            return url.strip()
        return url
    
    def load_config(self):
        """Load configuration from file if exists"""
        config = {
            #"qualtrics_url": "https://erasmusuniversity.eu.qualtrics.com/jfe/form/SV_b2CXRZP0xXfTWHc",
            #"qualtrics_redirect_url": "https://erasmusuniversity.eu.qualtrics.com/jfe/form/SV_b2CXRZP0xXfTWHc?completed=true&condition=${e://Field/CurrentCondition}",
            "conditions": [
                {"name": "random", "description": "Random Emotion System", "system": EmotionSystem.RANDOM.value},
                {"name": "rule_based", "description": "Rule-Based Emotion System", "system": EmotionSystem.RULE_BASED.value},
                {"name": "ml", "description": "Machine Learning Emotion System", "system": EmotionSystem.MACHINE_LEARNING.value}
            ],
            "game_time_limit": DEFAULT_TIME_LIMIT,
            "show_debug_info": False,
            "show_condition_info": False,
            "version_sequence": {
                "1": "random",
                "2": "rule_based",
                "3": "ml"
            },
            "verification_salt": "NPC_EMOTION_GAME_2024"
        }
        
        ## Create data folder if it doesn't exist
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
        
        ## Try to load existing config
        config_path = os.path.join(DATA_FOLDER, CONFIG_FILE)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    for key, value in saved_config.items():
                        if key in ["qualtrics_url", "qualtrics_redirect_url"] and value:
                            config[key] = self.clean_url(value)
                        elif key != "version_sequence": 
                            config[key] = value
            except Exception as e:
                print(f"Error loading config: {e}")
        
        ## Ensure we have a verification salt
        if "verification_salt" not in config:
            config["verification_salt"] = "NPC_EMOTION_GAME_2024"
        
        ## Ensure version_sequence is always fixed
        config["version_sequence"] = {"1": "random", "2": "rule_based", "3": "ml"}
        
        ## Save the config
        self.save_config(config)
        
        return config
    
    def save_config(self, config=None):
        # save configuration to file to inspect if necessary
        if config is None:
            config = self.config
        
        ## Clean URLs before saving
        if "qualtrics_url" in config:
            config["qualtrics_url"] = self.clean_url(config["qualtrics_url"])
        if "qualtrics_redirect_url" in config:
            config["qualtrics_redirect_url"] = self.clean_url(config["qualtrics_redirect_url"])
        
        ## Ensure version_sequence is always fixed
        config["version_sequence"] = {"1": "random", "2": "rule_based", "3": "ml"}
        
        config_path = os.path.join(DATA_FOLDER, CONFIG_FILE)
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def generate_verification_code(self, participant_id, version, condition):
        ## Generate a verification code based on participant ID, version, and condition
        if not participant_id or not version or not condition:
            return "INVALID"
        
        ## Get salt from config
        salt = self.config.get("verification_salt", "NPC_EMOTION_GAME_2024")
        
        ## Create a string to hash
        input_string = f"{salt}:{participant_id}:{version}:{condition}"
        
        ## Create a hash
        hash_obj = hashlib.sha256(input_string.encode())
        hash_bytes = hash_obj.digest()
        
        ## Convert to base64 and take first VERIFICATION_CODE_LENGTH characters
        code_full = base64.b64encode(hash_bytes).decode('utf-8')
        
        ## Remove any non-alphanumeric characters and take the first VERIFICATION_CODE_LENGTH
        code = ''.join(c for c in code_full if c.isalnum())[:VERIFICATION_CODE_LENGTH]
        
        ## Make sure the code is in uppercase for better readability
        return code.upper()
    
    def randomize_conditions(self):
        ## Return fixed condition order
        return {"1": "random", "2": "rule_based", "3": "ml"}
    
    def get_participant_condition_mapping(self, participant_id):
        ## Get condition mapping for this participant
        fixed_sequence = {"1": "random", "2": "rule_based", "3": "ml"}
        
        ## If participant ID is provided, store this fixed mapping for them
        if participant_id:
            ## Check if we already have a mapping for this participant
            completion_path = os.path.join(DATA_FOLDER, COMPLETION_FILE)
            if os.path.exists(completion_path):
                try:
                    with open(completion_path, 'r') as f:
                        all_completions = json.load(f)
                        if participant_id in all_completions and "version_sequence" in all_completions[participant_id]:
                            ## Return existing mapping - fixed
                            return all_completions[participant_id]["version_sequence"]
                except Exception as e:
                    print(f"Error loading condition mapping: {e}")
            
            ## Save the fixed sequence for this participant
            self.save_participant_condition_mapping(participant_id, fixed_sequence)
        
        return fixed_sequence
    
    def save_participant_condition_mapping(self, participant_id, version_sequence):
        ## Save the condition mapping for this participant
        if not participant_id:
            return False
                
        ## Load current completion data
        completion_path = os.path.join(DATA_FOLDER, COMPLETION_FILE)
        all_completions = {}
        
        if os.path.exists(completion_path):
            try:
                with open(completion_path, 'r') as f:
                    all_completions = json.load(f)
            except Exception:
                all_completions = {}
        
        ## Update mapping for this participant
        if participant_id not in all_completions:
            all_completions[participant_id] = {"1": False, "2": False, "3": False, "version_sequence": version_sequence}
        else:
            all_completions[participant_id]["version_sequence"] = version_sequence
        
        ## Save back to file
        try:
            with open(completion_path, 'w') as f:
                json.dump(all_completions, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving condition mapping: {e}")
            return False
    
    def load_completion_status(self, participant_id):
        ## Load participant's completion status
        if not participant_id:
            return {"1": False, "2": False, "3": False}
                
        ## Default status - no games completed
        status = {"1": False, "2": False, "3": False}
        
        ## Check if the completion status file exists
        completion_path = os.path.join(DATA_FOLDER, COMPLETION_FILE)
        if os.path.exists(completion_path):
            try:
                with open(completion_path, 'r') as f:
                    all_completions = json.load(f)
                    if participant_id in all_completions:
                        for key, value in all_completions[participant_id].items():
                            status[key] = value
            except Exception as e:
                print(f"Error loading completion status: {e}")
        
        ## Also check for result files to be sure
        for version in ["1", "2", "3"]:
            ## Get condition from mapping
            if "version_sequence" in status:
                condition = status["version_sequence"].get(version, "")
            else:
                ## Fixed sequence if no mapping found
                fixed_conditions = ["random", "rule_based", "ml"]
                condition = fixed_conditions[int(version) - 1] if int(version) <= len(fixed_conditions) else ""
                
            result_file = os.path.join(DATA_FOLDER, f"result_{participant_id}_{condition}.json")
            if os.path.exists(result_file):
                status[version] = True
        
        return status
    
    def save_completion_status(self, participant_id, version, completed=True):
        ## Save participant's completion status
        if not participant_id:
            return False
            
        ## Load current completion data
        completion_path = os.path.join(DATA_FOLDER, COMPLETION_FILE)
        all_completions = {}
        
        if os.path.exists(completion_path):
            try:
                with open(completion_path, 'r') as f:
                    all_completions = json.load(f)
            except Exception:
                all_completions = {}
        
        ## Update status for this participant
        if participant_id not in all_completions:
            ## Create participant entry with fixed condition sequence
            version_sequence = self.get_participant_condition_mapping(participant_id)
            all_completions[participant_id] = {"1": False, "2": False, "3": False, "version_sequence": version_sequence}
        
        all_completions[participant_id][version] = completed
        
        ## Save back to file
        try:
            with open(completion_path, 'w') as f:
                json.dump(all_completions, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving completion status: {e}")
            return False
    
    def get_next_version(self, participant_id):
        ## Get the next uncompleted game version for the participant
        status = self.load_completion_status(participant_id)
        
        ## Return the first uncompleted version
        for version in ["1", "2", "3"]:
            if not status.get(version, False):
                return version
        
        ## All versions completed
        return None
    
    ## Create UI widgets
    def create_widgets(self):
        ## Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ## Title
        title_label = ttk.Label(main_frame, text="NPC Emotion Game - Research Study", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        ## Notebook with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        ## Create tabs
        participant_tab = ttk.Frame(notebook)
        notebook.add(participant_tab, text="Participant Mode")
        
        ## Only add test and settings tabs in admin mode
        if self.admin_mode:
            test_tab = ttk.Frame(notebook)
            settings_tab = ttk.Frame(notebook)
            
            notebook.add(test_tab, text="Test Mode")
            notebook.add(settings_tab, text="Settings")
            
            ## Create content for test tab
            self.create_test_tab(test_tab)
            
            ## Create content for settings tab
            self.create_settings_tab(settings_tab)
        
        ## Create content for participant tab
        self.create_participant_tab(participant_tab)
        
        ## Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        ## Add a hidden keyboard shortcut to toggle admin mode
        self.root.bind('<Control-Alt-a>', self.toggle_admin_mode)
    
    def create_participant_tab(self, tab):
        ## Create the participant tab content with scrolling capability to get code
        ## Create a frame with scrollbar
        outer_frame = ttk.Frame(tab)
        outer_frame.pack(fill=tk.BOTH, expand=True)
        
        ## Add a canvas and scrollbar
        vscrollbar = ttk.Scrollbar(outer_frame, orient=tk.VERTICAL)
        vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas = tk.Canvas(outer_frame, yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        vscrollbar.config(command=canvas.yview)
        
        ## Create a frame inside the canvas to hold all content
        participant_frame = ttk.Frame(canvas, padding="20")
        
        ## Add the frame to the canvas
        canvas_window = canvas.create_window((0, 0), window=participant_frame, anchor="nw")
        
        ## Function to update the scrollregion when the frame changes size
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make sure the frame fills the canvas width
            canvas.itemconfig(canvas_window, width=event.width)
        
        ## Function to handle mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        ## Bind events for scrolling
        participant_frame.bind("<Configure>", configure_canvas)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows and MacOS (with shift)
        
        ## Instructions
        instructions = (
            "This launcher is for research participants in the NPC Emotion Study.\n\n"
            "To play the game:\n"
            "1. Enter your Participant ID from the survey\n"
            "2. Select which game version you need to play (1, 2, or 3)\n"
            "3. Click 'Launch Game' to play the selected version\n"
            "4. When finished, you will receive a verification code to enter in the survey"
        )
        
        instructions_label = ttk.Label(participant_frame, text=instructions, wraplength=700, justify="left")
        instructions_label.pack(pady=10)
        
        ## Participant ID Entry
        id_frame = ttk.Frame(participant_frame)
        id_frame.pack(pady=10)
        
        id_label = ttk.Label(id_frame, text="Participant ID:")
        id_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.participant_id_var = tk.StringVar()
        id_entry = ttk.Entry(id_frame, textvariable=self.participant_id_var, width=30)
        id_entry.pack(side=tk.LEFT)
        
        ## ID check button
        id_check_button = ttk.Button(id_frame, text="Check Progress", command=self.check_participant_progress)
        id_check_button.pack(side=tk.LEFT, padx=10)
        
        ## Game version selection
        version_frame = ttk.Frame(participant_frame)
        version_frame.pack(pady=10)
        
        version_label = ttk.Label(version_frame, text="Game Version:")
        version_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.version_var = tk.StringVar(value="1")
        version_radio1 = ttk.Radiobutton(version_frame, text="Version 1", variable=self.version_var, value="1")
        version_radio2 = ttk.Radiobutton(version_frame, text="Version 2", variable=self.version_var, value="2")
        version_radio3 = ttk.Radiobutton(version_frame, text="Version 3", variable=self.version_var, value="3")
        
        version_radio1.pack(side=tk.LEFT, padx=5)
        version_radio2.pack(side=tk.LEFT, padx=5)
        version_radio3.pack(side=tk.LEFT, padx=5)
        
        ## Progress display
        self.progress_var = tk.StringVar(value="")
        progress_label = ttk.Label(participant_frame, textvariable=self.progress_var, wraplength=700, justify="center")
        progress_label.pack(pady=10)
        
        ## Launch Game Button
        self.launch_game_button = ttk.Button(participant_frame, text="Launch Game", command=self.launch_participant_game)
        self.launch_game_button.pack(pady=20)
        
        ## Verification code display --> Hidden at the start
        self.verification_frame = ttk.Frame(participant_frame)
        
        verification_title = ttk.Label(self.verification_frame, text="Game Completed!", font=("Arial", 14, "bold"))
        verification_title.pack(pady=(0, 10))
        
        verification_instructions = ttk.Label(self.verification_frame, 
                                        text="Please copy the verification code below and enter it in the survey to continue:",
                                        wraplength=600)
        verification_instructions.pack(pady=(0, 10))
        
        self.verification_code_var = tk.StringVar(value="")
        verification_code_display = ttk.Entry(self.verification_frame, textvariable=self.verification_code_var, 
                                        width=10, font=("Arial", 16, "bold"), justify="center")
        verification_code_display.pack(pady=(0, 10))
        
        copy_button = ttk.Button(self.verification_frame, text="Copy Code", 
                            command=lambda: self.copy_to_clipboard(self.verification_code_var.get()))
        copy_button.pack(pady=(0, 10))
        
        return_instructions = ttk.Label(self.verification_frame, 
                                    text="Return to the survey and enter this code to continue.",
                                    wraplength=600)
        return_instructions.pack(pady=(0, 10))
        
        ## Add scrolling hint
        scroll_hint = ttk.Label(participant_frame, text="Scroll down if you can't see the verification code", 
                                font=("Arial", 9, "italic"), foreground="gray")
        scroll_hint.pack(pady=(30, 10))
        
        return participant_frame
    
    def copy_to_clipboard(self, text):
        ## Copy code to clipboard helper function
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("Verification code copied to clipboard!")
    
    def check_participant_progress(self):
        ## Check and display participant's progress
        participant_id = self.participant_id_var.get().strip()
        
        if not participant_id:
            messagebox.showerror("Error", "Please enter a Participant ID")
            return
        
        ## Load completion status
        status = self.load_completion_status(participant_id)
        
        ## Format progress message
        completed_count = sum(1 for v in status.values() if v and v != "version_sequence")
        progress_msg = f"Participant {participant_id} has completed {completed_count-1}/3 game versions.\n\n"
        
        for version in ["1", "2", "3"]:
            ## Show version number
            status_text = "✓ Completed" if status.get(version, False) else "❌ Not Completed"
            progress_msg += f"Version {version}: {status_text}\n"
        
        ## Suggest next version --> in sequence
        next_version = self.get_next_version(participant_id)
        if next_version:
            progress_msg += f"\nSuggested next version to play: Version {next_version}"
            self.version_var.set(next_version)
        else:
            progress_msg += "\nAll versions completed!"
        
        ## Update progress display
        self.progress_var.set(progress_msg)
        self.status_var.set(f"Checked progress for participant {participant_id}")
    
    def create_test_tab(self, tab):
        ## Create the test tab content
        test_frame = ttk.Frame(tab, padding="10")
        test_frame.pack(fill=tk.BOTH, expand=True)
        
        test_instructions = (
            "This test mode allows to run each version of the game directly.\n"
            "Select the emotion system to test and click 'Launch Test Game'."
        )
        
        test_instructions_label = ttk.Label(test_frame, text=test_instructions, wraplength=700, justify="left")
        test_instructions_label.pack(pady=10)
        
        ## Condition Selection
        condition_frame = ttk.Frame(test_frame)
        condition_frame.pack(pady=10)
        
        condition_label = ttk.Label(condition_frame, text="Select Emotion System:")
        condition_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.condition_var = tk.StringVar()
        if self.config["conditions"]:
            self.condition_var.set(self.config["conditions"][0]["description"])
        
        condition_options = [cond["description"] for cond in self.config["conditions"]]
        condition_menu = ttk.Combobox(condition_frame, textvariable=self.condition_var, values=condition_options, state="readonly")
        condition_menu.pack(side=tk.LEFT)
        
        ## Test Participant ID 
        test_id_frame = ttk.Frame(test_frame)
        test_id_frame.pack(pady=10)
        
        test_id_label = ttk.Label(test_id_frame, text="Test Participant ID (optional):")
        test_id_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_id_var = tk.StringVar()
        self.test_id_var.set("test_user")
        test_id_entry = ttk.Entry(test_id_frame, textvariable=self.test_id_var, width=30)
        test_id_entry.pack(side=tk.LEFT)
        
        ## Launch Test Button
        test_button = ttk.Button(test_frame, text="Launch Test Game", command=self.launch_test_game)
        test_button.pack(pady=20)
        
        ## Verification codes testing area
        verification_test_frame = ttk.LabelFrame(test_frame, text="Verification Code Testing", padding=10)
        verification_test_frame.pack(fill=tk.X, pady=20)
        
        test_pid_frame = ttk.Frame(verification_test_frame)
        test_pid_frame.pack(fill=tk.X, pady=5)
        test_pid_label = ttk.Label(test_pid_frame, text="Participant ID:")
        test_pid_label.pack(side=tk.LEFT, padx=(0, 10))
        self.test_v_pid_var = tk.StringVar(value="test_user")
        test_pid_entry = ttk.Entry(test_pid_frame, textvariable=self.test_v_pid_var, width=20)
        test_pid_entry.pack(side=tk.LEFT)
        
        test_version_frame = ttk.Frame(verification_test_frame)
        test_version_frame.pack(fill=tk.X, pady=5)
        test_version_label = ttk.Label(test_version_frame, text="Version:")
        test_version_label.pack(side=tk.LEFT, padx=(0, 10))
        self.test_v_version_var = tk.StringVar(value="1")
        test_version_combo = ttk.Combobox(test_version_frame, textvariable=self.test_v_version_var, 
                                       values=["1", "2", "3"], state="readonly", width=5)
        test_version_combo.pack(side=tk.LEFT)
        
        test_gen_button = ttk.Button(verification_test_frame, text="Generate Test Code", 
                                   command=self.generate_test_verification_code)
        test_gen_button.pack(pady=10)
        
        self.test_code_var = tk.StringVar(value="")
        test_code_label = ttk.Label(verification_test_frame, textvariable=self.test_code_var,
                                 font=("Arial", 14, "bold"))
        test_code_label.pack(pady=5)
    
    def generate_test_verification_code(self):
        ## Test verification code for debugging
        pid = self.test_v_pid_var.get().strip()
        version = self.test_v_version_var.get()
        
        if not pid:
            self.test_code_var.set("Enter a participant ID")
            return
        
        ## Get the condition for this version --> always use the fixed mapping
        fixed_sequence = {"1": "random", "2": "rule_based", "3": "ml"}
        condition = fixed_sequence.get(version, "random")
        
        ## Generate code
        code = self.generate_verification_code(pid, version, condition)
        self.test_code_var.set(f"Code: {code}")
        
        ## Also copy to clipboard for testing
        self.copy_to_clipboard(code)
    
    def create_settings_tab(self, tab):
        ## Create the settings tab content
        settings_frame = ttk.Frame(tab, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ## Qualtrics URL --> not working
        url_frame = ttk.Frame(settings_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        url_label = ttk.Label(url_frame, text="Qualtrics Survey URL:")
        url_label.pack(anchor=tk.W)
        
        self.url_var = tk.StringVar(value=self.clean_url(self.config["qualtrics_url"]))
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.pack(fill=tk.X, pady=5)
        
        ## Qualtrics URL --> not working
        redirect_frame = ttk.Frame(settings_frame)
        redirect_frame.pack(fill=tk.X, pady=5)
        
        redirect_label = ttk.Label(redirect_frame, text="Qualtrics Redirect URL:")
        redirect_label.pack(anchor=tk.W)
        
        self.redirect_var = tk.StringVar(value=self.clean_url(self.config["qualtrics_redirect_url"]))
        redirect_entry = ttk.Entry(redirect_frame, textvariable=self.redirect_var, width=60)
        redirect_entry.pack(fill=tk.X, pady=5)
        
        ## Verification Salt
        salt_frame = ttk.Frame(settings_frame)
        salt_frame.pack(fill=tk.X, pady=5)
        
        salt_label = ttk.Label(salt_frame, text="Verification Code Salt:")
        salt_label.pack(anchor=tk.W)
        
        self.salt_var = tk.StringVar(value=self.config.get("verification_salt", "NPC_EMOTION_GAME_2024"))
        salt_entry = ttk.Entry(salt_frame, textvariable=self.salt_var, width=40)
        salt_entry.pack(fill=tk.X, pady=5)
        
        ## Version Sequence
        sequence_frame = ttk.Frame(settings_frame)
        sequence_frame.pack(fill=tk.X, pady=5)
        
        sequence_label = ttk.Label(sequence_frame, text="Version Sequence:")
        sequence_label.pack(anchor=tk.W)
        
        ## Version 1 condition
        v1_frame = ttk.Frame(settings_frame)
        v1_frame.pack(fill=tk.X, pady=2)
        v1_label = ttk.Label(v1_frame, text="Version 1:")
        v1_label.pack(side=tk.LEFT, padx=(20, 10))
        
        self.v1_var = tk.StringVar(value="random")
        v1_entry = ttk.Entry(v1_frame, textvariable=self.v1_var, state="readonly", width=15)
        v1_entry.pack(side=tk.LEFT)
        
        ## Version 2 condition
        v2_frame = ttk.Frame(settings_frame)
        v2_frame.pack(fill=tk.X, pady=2)
        v2_label = ttk.Label(v2_frame, text="Version 2:")
        v2_label.pack(side=tk.LEFT, padx=(20, 10))
        
        self.v2_var = tk.StringVar(value="rule_based")
        v2_entry = ttk.Entry(v2_frame, textvariable=self.v2_var, state="readonly", width=15)
        v2_entry.pack(side=tk.LEFT)
        
        ## Version 3 condition
        v3_frame = ttk.Frame(settings_frame)
        v3_frame.pack(fill=tk.X, pady=2)
        v3_label = ttk.Label(v3_frame, text="Version 3:")
        v3_label.pack(side=tk.LEFT, padx=(20, 10))
        
        self.v3_var = tk.StringVar(value="ml")
        v3_entry = ttk.Entry(v3_frame, textvariable=self.v3_var, state="readonly", width=15)
        v3_entry.pack(side=tk.LEFT)
        
        ## Game Time Limit
        time_frame = ttk.Frame(settings_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        time_label = ttk.Label(time_frame, text="Game Time Limit (seconds):")
        time_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.time_var = tk.IntVar(value=self.config["game_time_limit"])
        time_entry = ttk.Spinbox(time_frame, from_=30, to=600, increment=30, textvariable=self.time_var, width=5)
        time_entry.pack(side=tk.LEFT)
        
        ## Debug Info Checkbox
        debug_frame = ttk.Frame(settings_frame)
        debug_frame.pack(fill=tk.X, pady=5)
        
        self.debug_var = tk.BooleanVar(value=self.config["show_debug_info"])
        debug_check = ttk.Checkbutton(debug_frame, text="Show Debug Info (emotion/reaction names)", variable=self.debug_var)
        debug_check.pack(anchor=tk.W)
        
        ## Add condition display toggle
        show_condition_frame = ttk.Frame(settings_frame)
        show_condition_frame.pack(fill=tk.X, pady=5)
        
        self.show_condition_var = tk.BooleanVar(value=self.config.get("show_condition_info", False))
        show_condition_check = ttk.Checkbutton(show_condition_frame, 
                                           text="Show Condition Info (for testing only)", 
                                           variable=self.show_condition_var)
        show_condition_check.pack(anchor=tk.W)
        
        ## Save Settings Button
        save_settings_button = ttk.Button(settings_frame, text="Save Settings", command=self.save_settings)
        save_settings_button.pack(pady=20)
        
        ## Reset Completion Data Button (for admin use omly)
        reset_button = ttk.Button(settings_frame, text="Reset All Completion Data", command=self.reset_completion_data)
        reset_button.pack(pady=5)
    
    def reset_completion_data(self):
        """Reset all completion data (admin function)"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset ALL participant completion data? This cannot be undone."):
            completion_path = os.path.join(DATA_FOLDER, COMPLETION_FILE)
            if os.path.exists(completion_path):
                try:
                    os.remove(completion_path)
                    messagebox.showinfo("Reset Complete", "All completion data has been reset.")
                except Exception as e:
                    messagebox.showerror("Reset Error", f"Could not reset data: {e}")
            else:
                messagebox.showinfo("Reset Complete", "No completion data to reset.")
    
    def toggle_admin_mode(self, event=None):
        ## Adming mode toggling
        ## Destroy and recreate the UI with new admin mode
        self.admin_mode = not self.admin_mode
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_widgets()
        
        ## Show a subtle indicator when toggling to admin mode
        if self.admin_mode:
            self.status_var.set("Admin mode enabled")
        else:
            self.status_var.set("Admin mode disabled")
    
    def check_command_line_args(self):
        ## Check if launcher was started with URL parameters
        if len(sys.argv) > 1 and sys.argv[1].startswith("npcgame://"):
            self.handle_url_protocol(sys.argv[1])
    
    def handle_url_protocol(self, url):
        ## Handle custom URL protocol for launching from Qualtrics --> NOT WORKING
        try:
            ## Parse the URL
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            ## Check for participant ID
            if 'pid' in params:
                participant_id = params['pid'][0]
                self.participant_id_var.set(participant_id)
                
                ## Automatically check progress
                self.check_participant_progress()
                
                ## Check for version 
                if 'version' in params:
                    version = params['version'][0]
                    if version in ["1", "2", "3"]:
                        self.version_var.set(version)
                
                ## Check for condition
                if 'condition' in params:
                    condition = params['condition'][0]
                    
                    ## Auto-launch the game with this condition
                    print(f"Auto-launching game for participant {participant_id} with condition {condition}")
                    self.status_var.set(f"Auto-launching: Participant {participant_id}, Condition {condition}")
                    
                    ## Determine which version this corresponds to and set it
                    fixed_sequence = {"1": "random", "2": "rule_based", "3": "ml"}
                    for version, cond in fixed_sequence.items():
                        if cond == condition:
                            self.version_var.set(version)
                            break
                    
                    ## Launch the game
                    self.launch_participant_game(condition)
                else:
                    messagebox.showinfo("Participant ID Received", 
                                     f"Participant ID {participant_id} loaded.\nPlease select a game version and click 'Launch Game'.")
        except Exception as e:
            messagebox.showerror("URL Protocol Error", f"Error processing URL: {e}")
    
    def open_survey(self):
        ## Open the Qualtrics survey in a web browser --> attepmted but does not work, keep as proof of attempt
        try:
            url = self.clean_url(self.config["qualtrics_url"])
            webbrowser.open(url)
            self.status_var.set(f"Opened survey: {url}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open survey: {e}")
    
    def get_condition_system(self, condition_name):
        ## Get the emotion system class for the given condition name
        for cond in self.config["conditions"]:
            if cond["name"] == condition_name or cond["description"] == condition_name:
                system_type = cond["system"]
                if system_type == EmotionSystem.RANDOM.value:
                    return RandomEmotionSystem()
                elif system_type == EmotionSystem.RULE_BASED.value:
                    return RuleBasedEmotionSystem()
                elif system_type == EmotionSystem.MACHINE_LEARNING.value:
                    return MLEmotionSystem()
        
        ## Default to random if not found
        print(f"Warning: Condition {condition_name} not found, defaulting to Random")
        return RandomEmotionSystem()
    
    def get_condition_for_version(self, version):
        ## Get the condition name for the specified version for this participant
        ## Always use fixed mapping for versions
        fixed_sequence = {"1": "random", "2": "rule_based", "3": "ml"}
        return fixed_sequence.get(version, "random")
    
    def show_verification_code(self, participant_id, version, condition):
        ## Show the verification code to the user
        ## Generate the verification code
        code = self.generate_verification_code(participant_id, version, condition)
        
        ## Update the verification code display
        self.verification_code_var.set(code)
        
        ## Show the verification frame
        self.verification_frame.pack(pady=10)
        
        ## Force window to update
        self.root.update()
        
        ## Copy to clipboard automatically
        self.copy_to_clipboard(code)
        
        ## Return the code
        return code
    
    def launch_participant_game(self, condition=None):
        ## Launch game for a research participant 
        ## Clean up participant ID
        participant_id = self.participant_id_var.get().strip()
        
        if not participant_id:
            messagebox.showerror("Error", "Please enter a Participant ID")
            return
        
        ## Get the selected version
        version = self.version_var.get()
        
        ## Determine condition if not specified
        if condition is None:
            condition = self.get_condition_for_version(version)
        
        ## Check if this version is already completed
        status = self.load_completion_status(participant_id)
        if status.get(version, False):
            if not messagebox.askyesno("Version Already Completed", 
                               f"It appears that participant {participant_id} has already completed Version {version}.\n\nDo you want to play it again anyway?"):
                return
        
        ## Run the game !!
        self.status_var.set(f"Launching: Participant {participant_id}, Version {version}")
        
        try:
            ## Hide the verification frame if it's visible
            self.verification_frame.pack_forget()
            
            ## Hide the launcher window while the game runs
            self.root.withdraw()
            
            ## Get the emotion system
            emotion_system = self.get_condition_system(condition)
            
            ## Create and run the game
            game = Game(
                emotion_system_instance=emotion_system,
                game_time_limit=self.config["game_time_limit"],
                show_debug_info=self.config.get("show_debug_info", False),
                participant_id=participant_id,
                condition=condition
            )
            
            ## Run the game and get results
            result = game.run()
            
            ## Save the results to a file
            if result:
                self.save_results(result)
                
                ## Mark this version as completed
                self.save_completion_status(participant_id, version, True)
                
                ## Update the progress display
                self.check_participant_progress()
            
            ## Show the launcher window again so the player can play the next one
            self.root.deiconify()
            
            ## Show verification code if the game was completed
            if result and result.get("completed", False):
                ## Show verification code
                verification_code = self.show_verification_code(participant_id, version, condition)
                
                ## Store the verification code in the results file
                if verification_code:
                    result["verification_code"] = verification_code
                    self.save_results(result)
            
        except Exception as e:
            self.root.deiconify()
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Game Error", f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
    
    def launch_test_game(self):
        ## Launch game in test mode
        condition = self.condition_var.get()
        participant_id = self.test_id_var.get().strip() if self.test_id_var.get().strip() else None
        
        self.status_var.set(f"Launching test game: {condition}")
        
        try:
            ## extract the emotion system
            emotion_system = self.get_condition_system(condition)
            
            ## Hide the launcher window while the game runs
            self.root.withdraw()
            
            ## Create and run the game
            game = Game(
                emotion_system_instance=emotion_system,
                game_time_limit=self.config["game_time_limit"],
                show_debug_info=True, 
                participant_id=participant_id,
                condition=condition
            )
            
            ## Run the game
            result = game.run()
            
            ## Save the results in relation to participant ID
            if result and participant_id:
                self.save_results(result)
                
                ## Get the version number based on the condition
                fixed_sequence = {"1": "random", "2": "rule_based", "3": "ml"}
                version = next(
                    (ver for ver, cond in fixed_sequence.items() if cond == condition),
                    "1"  ## Default to random condition
                )
                
                ## Show verification code for testing
                self.show_verification_code(participant_id, version, condition)
            
            ## Show the launcher window again
            self.root.deiconify()
            
            self.status_var.set("Test game completed")
            
        except Exception as e:
            self.root.deiconify()
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Game Error", f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
    
    def save_results(self, result):
        ## Save results for later use
        if not result:
            return
        
        try:
            if not os.path.exists(DATA_FOLDER):
                os.makedirs(DATA_FOLDER)
            
            filename = f"result_{result['participant_id']}_{result['condition']}.json"
            filepath = os.path.join(DATA_FOLDER, filename)
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=4)
            
            print(f"Results saved to {filepath}")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def save_settings(self):
        ## Save settings from the settings tab
        try:
            ## Update config with current values --> cleaned
            self.config["qualtrics_url"] = self.clean_url(self.url_var.get())
            self.config["qualtrics_redirect_url"] = self.clean_url(self.redirect_var.get())
            self.config["game_time_limit"] = self.time_var.get()
            self.config["show_debug_info"] = self.debug_var.get()
            self.config["show_condition_info"] = self.show_condition_var.get()
            self.config["verification_salt"] = self.salt_var.get()
            
            ## Fixed version sequence
            self.config["version_sequence"] = {"1": "random", "2": "rule_based", "3": "ml"}
            
            ## Save config to file
            if self.save_config():
                ## Reload the configuration to ensure it's updated
                self.config = self.load_config()
                
                self.status_var.set("Settings saved")
                messagebox.showinfo("Settings", "Settings saved successfully")
            else:
                self.status_var.set("Error saving settings")
                messagebox.showerror("Settings Error", "Could not save settings. Check file permissions.")
        except Exception as e:
            self.status_var.set(f"Error saving settings: {e}")
            messagebox.showerror("Settings Error", f"Could not save settings: {e}")

## Register URL protocol handler if on Windows
def register_protocol_handler():
    ## Register the custom URL protocol for Windows
    if sys.platform == 'win32':
        try:
            import winreg
            
            ## Get the full path to the executable
            executable = sys.executable
            script = os.path.abspath(sys.argv[0])
            
            ## Register the protocol
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\npcgame") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "URL:NPC Game Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
                
                with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                    if script.endswith('.py'):
                        ## Running as script
                        cmd = f'"{executable}" "{script}" "%1"'
                    else:
                        ## Running as executable
                        cmd = f'"{script}" "%1"'
                    winreg.SetValue(cmd_key, "", winreg.REG_SZ, cmd)
            
            print("Protocol handler registered successfully")
        except Exception as e:
            print(f"Could not register protocol handler: {e}")

## Main function
def main():
    ## Check for admin mode flag
    admin_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "--admin":
        admin_mode = True
        ## Remove the admin flag so it doesn't interfere with URL handling
        sys.argv.pop(1)
    
    ## Register protocol handler
    register_protocol_handler()
    
    ## Create and run the launcher app
    root = tk.Tk()
    app = LauncherApp(root, admin_mode)
    root.mainloop()

if __name__ == "__main__":
    main()