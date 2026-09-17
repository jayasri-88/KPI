import os
import glob

# Find and remove __init__.py in models directory
models_dir = glob.glob("app/models/__init__.py")
for f in models_dir:
    os.remove(f)
    print(f"Removed: {f}")

# Also check for _init__.py
_init_files = glob.glob("app/models/_init__.py")
for f in _init_files:
    os.remove(f)
    print(f"Removed: {f}")