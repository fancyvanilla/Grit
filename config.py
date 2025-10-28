import os
from pathlib import Path
from dotenv import load_dotenv
import ctypes

load_dotenv()  

def hide_grit():
    GRIT_MODE = os.getenv("GRIT_MODE", "dev")
    GRIT_FOLDER = Path(".grit").resolve()
    if GRIT_MODE != "dev":
        if os.name == "nt":  # Windows
            if GRIT_FOLDER.exists():
                ctypes.windll.kernel32.SetFileAttributesW(str(GRIT_FOLDER), 0x02)
        else:  # macOS/Linux: prefix with . makes it hidden
            if GRIT_FOLDER.exists() and not GRIT_FOLDER.name.startswith("."):
                GRIT_FOLDER.rename(GRIT_FOLDER.parent / f".{GRIT_FOLDER.name}")
