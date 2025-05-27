#!/usr/bin/env python3
"""
Build script for the NPC Emotion Game research study
Creates a standalone executable using PyInstaller with XGBoost support
"""

import os
import sys
import shutil
import subprocess
import argparse
import platform
import importlib.util
import glob
import site

def find_xgboost_dylib():
    """Find the XGBoost dynamic library file"""
    print("Searching for XGBoost library...")
    
    ## Check if xgboost is installed
    if importlib.util.find_spec("xgboost") is None:
        print("XGBoost is not installed. Please install it with: pip install xgboost")
        return None
    
    ## Get xgboost module path
    import xgboost as xgb
    xgboost_path = os.path.dirname(xgb.__file__)
    print(f"XGBoost module path: {xgboost_path}")
    
    # Look for libxgboost.dylib in various locations
    potential_paths = [
        os.path.join(xgboost_path, 'lib', 'libxgboost.dylib'),
        os.path.join(xgboost_path, 'lib64', 'libxgboost.dylib'),
        os.path.join(xgboost_path, '..', 'lib', 'libxgboost.dylib'),
        os.path.join(xgboost_path, 'libxgboost.dylib'),
        os.path.join(os.path.dirname(xgboost_path), 'lib', 'libxgboost.dylib')
    ]
    
    ## Add site-packages paths
    for site_dir in site.getsitepackages():
        potential_paths.extend([
            os.path.join(site_dir, 'xgboost', 'lib', 'libxgboost.dylib'),
            os.path.join(site_dir, 'lib', 'libxgboost.dylib')
        ])
    
    ## Search for any libxgboost files if the standard locations don't work
    if platform.system() == 'Darwin':
        # On macOS, search in common library locations
        for lib_dir in ['/usr/local/lib', '/usr/lib', os.path.expanduser('~/lib')]:
            potential_paths.append(os.path.join(lib_dir, 'libxgboost.dylib'))
        
        ## Use find command to locate the file anywhere in the system
        try:
            import subprocess
            find_result = subprocess.run(['find', '/', '-name', 'libxgboost.dylib', '-type', 'f', '-not', '-path', '*/\.*'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            if find_result.returncode == 0 and find_result.stdout:
                for path in find_result.stdout.strip().split('\n'):
                    if path:
                        potential_paths.append(path)
        except Exception as e:
            print(f"Error searching for libxgboost.dylib: {e}")
    
    ## For Windows specifically, look for the .dll file
    if platform.system() == 'Windows':
        for site_dir in site.getsitepackages():
            dll_files = glob.glob(os.path.join(site_dir, '**', 'xgboost.dll'), recursive=True)
            potential_paths.extend(dll_files)
        
        ## Check XGBoost installation directory for DLL
        import xgboost as xgb
        xgboost_dir = os.path.dirname(xgb.__file__)
        dll_files = glob.glob(os.path.join(xgboost_dir, '**', 'xgboost.dll'), recursive=True)
        potential_paths.extend(dll_files)
    
    ## Check all potential paths
    for path in potential_paths:
        if os.path.exists(path):
            print(f"Found XGBoost library at: {path}")
            return path
    
    print("Warning: Could not find XGBoost library. The application may not work correctly.")
    return None
## Create XGBoost version fixing system in case issues arise with version control
def create_xgboost_version_fix():
    """Create the XGBoost VERSION fixer script"""
    script_content = """# xgboost_VERSION_fix.py
import os
import sys
import shutil

def fix_xgboost_version():
    \"\"\"Create the XGBoost VERSION file in the correct location\"\"\"
    try:
        # Get the location of the executable
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        
        # Create VERSION file directly in the xgboost directory
        xgboost_dir = os.path.join(base_dir, 'xgboost')
        if not os.path.exists(xgboost_dir):
            os.makedirs(xgboost_dir)
            
        version_file = os.path.join(xgboost_dir, 'VERSION')
        with open(version_file, 'w') as f:
            f.write('3.0.0')
            
        print(f"Created XGBoost VERSION file at: {version_file}")
        return True
    except Exception as e:
        print(f"Error creating XGBoost VERSION file: {e}")
        return False
"""
    
    ## Write the script to a file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, 'xgboost_VERSION_fix.py')
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"Created XGBoost VERSION fix script at: {script_path}")
    return script_path

def main():
    ## Parse command line arguments
    parser = argparse.ArgumentParser(description="Build the NPC Emotion Game executable")
    parser.add_argument('--clean', action='store_true', help='Clean build directories before building')
    parser.add_argument('--onefile', action='store_true', help='Create a single executable file')
    parser.add_argument('--noconfirm', action='store_true', help='Replace output directory without asking')
    parser.add_argument('--debug', action='store_true', help='Include debug information in the build')
    args = parser.parse_args()

    ## Define build directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(base_dir, 'build')
    dist_dir = os.path.join(base_dir, 'dist')
    
    ## Clean build directories if requested
    if args.clean:
        print("Cleaning build directories...")
        for dir_path in [build_dir, dist_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
    
    ## Ensure the model directory is present
    model_dir = os.path.join(base_dir, 'model')
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print(f"Created empty model directory at {model_dir}")
        print("Note: You need to place your model file (game_npc_model.pkl) in the model directory")
    
    ## Check if the model file exists
    model_file = os.path.join(model_dir, 'game_npc_model.pkl')
    if not os.path.exists(model_file):
        print("Warning: Model file not found. The ML condition will fall back to rule-based behavior.")
        print(f"Expected location: {model_file}")
    
    ## Create data directory if it doesn't exist
    data_dir = os.path.join(base_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory at {data_dir}")
    
    ## Create XGBoost VERSION fix script
    version_fix_script = create_xgboost_version_fix()
    
    ## Create XGBoost VERSION file for inclusion
    import xgboost as xgb
    xgboost_dir = os.path.dirname(xgb.__file__)
    
    ## Get VERSION content from installed xgboost if available, otherwise use default
    version_content = "3.0.0"  # Default
    src_version_file = os.path.join(xgboost_dir, "VERSION")
    if os.path.exists(src_version_file):
        with open(src_version_file, 'r') as f:
            version_content = f.read().strip()
    
    ## Create VERSION file in a temporary directory
    temp_dir = os.path.join(base_dir, 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    xgboost_temp_dir = os.path.join(temp_dir, 'xgboost')
    if not os.path.exists(xgboost_temp_dir):
        os.makedirs(xgboost_temp_dir)
    
    temp_version_file = os.path.join(xgboost_temp_dir, 'VERSION')
    with open(temp_version_file, 'w') as f:
        f.write(version_content)
    
    ## Build the PyInstaller command
    pyinstaller_args = ['pyinstaller', '--clean']
    
    ## Add onefile option for further debugging
    if args.onefile:
        pyinstaller_args.append('--onefile')
    else:
        pyinstaller_args.append('--onedir')
    
    ## Add noconfirm option
    if args.noconfirm:
        pyinstaller_args.append('--noconfirm')
    
    ## Add console flag for debug builds
    if args.debug:
        pyinstaller_args.append('--console')
    else:
        pyinstaller_args.append('--noconsole')
    
    pyinstaller_args.append('--windowed')

    ## Find XGBoost library
    xgboost_lib = find_xgboost_dylib()
    
    ## Add required modules and dependencies
    pyinstaller_args.extend([
        '--hidden-import=xgboost',
        '--hidden-import=scipy',
        '--hidden-import=numpy',
        '--hidden-import=joblib',
        '--hidden-import=scipy.sparse._csr',
        '--hidden-import=scipy.sparse._csc',
        '--hidden-import=scipy.sparse._coo',
        '--hidden-import=scipy.special.cython_special',
        '--collect-submodules=numpy',
        '--collect-submodules=scipy',
        '--collect-submodules=xgboost',
        '--collect-data=xgboost'
    ])

    ## Add the XGBoost if found
    if xgboost_lib:
        if platform.system() == 'Darwin':
            # On macOS, place the dylib in the lib directory
            pyinstaller_args.extend(['--add-binary', f'{xgboost_lib}{os.pathsep}lib'])
        elif platform.system() == 'Windows':
            # On Windows, place the DLL in the root directory
            pyinstaller_args.extend(['--add-binary', f'{xgboost_lib}{os.pathsep}.'])
    
    ## For macOS --> add specific options to avoid the pygame/tkinter conflict
    if platform.system() == 'Darwin':
        pyinstaller_args.extend([
            '--hidden-import=pygame',
            '--collect-submodules=pygame',
            '--collect-data=pygame'
        ])
    
    ## Add icon if available
    icon_file = os.path.join(base_dir, 'resources', 'icon.ico') if platform.system() == 'Windows' else \
                os.path.join(base_dir, 'resources', 'icon.icns') if platform.system() == 'Darwin' else None
    
    if icon_file and os.path.exists(icon_file):
        pyinstaller_args.extend(['--icon', icon_file])
    
    ## Add name of the game 
    pyinstaller_args.extend(['--name', 'NPC_Emotion_Game'])
    
    ## Add data files and directories
    data_args = []
    
    ## Add model directory
    data_args.extend(['--add-data', f'{model_dir}{os.pathsep}model'])
    
    ## Add VERSION fixer script
    data_args.extend(['--add-data', f'{version_fix_script}{os.pathsep}.'])
    
    ## Add xgboost VERSION file directly to xgboost directory
    data_args.extend(['--add-data', f'{xgboost_temp_dir}{os.pathsep}xgboost'])
    
    ## Add resources directory if it exists - properly handle this conditional
    if os.path.exists(os.path.join(base_dir, "resources")):
        data_args.extend(['--add-data', f'{os.path.join(base_dir, "resources")}{os.pathsep}resources'])
    
    ##Add all the data arguments to the PyInstaller arguments
    pyinstaller_args.extend(data_args)
    
    
    ## This is the entry point for the application w
    pyinstaller_args.append('launcher.py')
    
    ## Print the command
    print("Running PyInstaller with:")
    print(" ".join(pyinstaller_args))
    
    ## Run PyInstaller to actually build the game itself
    try:
        subprocess.run(pyinstaller_args, check=True)
        print("Build completed successfully!")
        
        ## Print the output directory
        if args.onefile:
            output_file = os.path.join(dist_dir, 'NPC_Emotion_Game.exe' if platform.system() == 'Windows' else 'NPC_Emotion_Game')
            print(f"Executable created at: {output_file}")
        else:
            output_dir = os.path.join(dist_dir, 'NPC_Emotion_Game')
            print(f"Application created at: {output_dir}")
        
        ## Post-build verification for XGBoost library    
        if args.onefile:
            print("\nChecking executable:")
            print("The XGBoost library was included in the build process.")
            print("If you still encounter XGBoost errors, please try using --onedir mode instead.")
        else:
            if platform.system() == 'Darwin':
                lib_dir = os.path.join(dist_dir, 'NPC_Emotion_Game', 'lib')
                if os.path.exists(lib_dir):
                    lib_files = os.listdir(lib_dir)
                    xgboost_found = any('xgboost' in f.lower() for f in lib_files)
                    print(f"\nXGBoost library found in output directory: {xgboost_found}")
                    if xgboost_found:
                        print(f"XGBoost library files: {[f for f in lib_files if 'xgboost' in f.lower()]}")
                    else:
                        print("Warning: XGBoost library not found in the output directory.")
                
                ## Check if XGBoost VERSION file exists in the correct location
                xgboost_dir = os.path.join(dist_dir, 'NPC_Emotion_Game', 'xgboost')
                if os.path.exists(xgboost_dir):
                    version_file = os.path.join(xgboost_dir, 'VERSION')
                    if os.path.exists(version_file):
                        print(f"XGBoost VERSION file found at: {version_file}")
                    else:
                        print("Warning: XGBoost VERSION file not found in output directory.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())