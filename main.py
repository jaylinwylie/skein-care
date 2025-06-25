import sys
import os
import json
import wx

from skein import Catalog
import ui

app = wx.App()
library: dict[str, dict[str, int]] = {}
catalog = Catalog()

print("Loading catalogs")
catalogs_dir = "catalogs"
if not os.path.exists(catalogs_dir):
    os.makedirs(catalogs_dir)
for filename in os.listdir(catalogs_dir):
    if filename.endswith(".json") and not filename.startswith("_"):
        brand = os.path.splitext(filename)[0]
        try:
            print(f"Loading catalog {filename}")
            with open(os.path.join(catalogs_dir, filename)) as f:
                data = json.load(f)
            catalog.load_brand(brand, data)
        except Exception as e:
            print(f"Error loading catalog {filename}: {e}")

library_file = "library.json"
if os.path.exists(library_file):
    try:
        print("Loading library")
        with open(library_file, 'r') as f1:
            library = json.load(f1)
        print("Library loaded successfully.")
    except Exception as e:
        print(f"Error loading library: {e}")
else:
    print("Library file not found, creating new library.")
    library = {}
    with open(library_file, 'w') as f2:
        json.dump(library, f2, indent=4) 

print("Creating main window")
window = ui.Window(library, catalog)

window.Show()
app.SetTopWindow(window)

print("Starting main loop")
exit_code = app.MainLoop()

print("Saving library")
library_file = "library.json"
try:
    with open(library_file, 'w') as f:
        json.dump(library, f, indent=4)
except Exception as e:
    print(f"Error saving library: {e}")

print("Exiting")
sys.exit(exit_code)
