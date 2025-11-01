import ctypes
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

def hide_grit():
    GRIT_MODE = os.getenv("GRIT_MODE", "prod") # You can set GRIT_MODE=dev to disable hiding
    GRIT_FOLDER = Path(".grit").resolve()
    if GRIT_MODE == "dev":
        return
    
    # For windows, we set the hidden attribute and for macos/linux the folder name starts with a dot
    if GRIT_FOLDER.exists() and os.name == "nt":
        FILE_ATTRIBUTE_HIDDEN = 0x02
        try:
            ret = ctypes.windll.kernel32.SetFileAttributesW(str(GRIT_FOLDER), FILE_ATTRIBUTE_HIDDEN)
            if ret == 0:
                print(f"Failed to hide {GRIT_FOLDER}")
        except Exception as e:
            print(f"Error hiding folder: {e}")