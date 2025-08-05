import sys
import os
import json
import wx

from skein import Catalog
from ui import Window
from model import SkeinModel


app = wx.App()
library: dict[str, dict[str, int]] = {}
catalog: Catalog = Catalog()

print("Loading catalogs...")
catalogs_dir = "catalogs"
if not os.path.exists(catalogs_dir):
    os.makedirs(catalogs_dir)

for filename in os.listdir(catalogs_dir):
    if filename.endswith(".json") and not filename.startswith("_"):
        brand = os.path.splitext(filename)[0]

        try:
            with open(os.path.join(catalogs_dir, filename)) as f:
                data = json.load(f)
            catalog.load_brand(brand, data)
        except Exception as e:
            print(f"Error loading catalog {filename}: {e}")

print("Loading library...")
library_file = "library.json"
if os.path.exists(library_file):
    try:
        with open(library_file, 'r') as f1:
            library = json.load(f1)
    except Exception as e:
        print(f"Error loading library: {e}")
else:
    print("Library file not found, creating new library.")
    library = {}
    with open(library_file, 'w') as f2:
        json.dump(library, f2, indent=4)

print("Loading defaults...")
defaults = {}
defaults_file = "defaults.json"
if os.path.exists(defaults_file):
    try:
        with open(defaults_file, 'r') as f:
            defaults = json.load(f)
    except Exception as e:
        print(f"Error loading defaults: {e}")
else:
    print("Defaults file not found, creating new defaults.")
    with open(defaults_file, 'w') as f:
        json.dump(defaults or {}, f, indent=4)

print("Creating model...")
model = SkeinModel(library, catalog)

print("Creating main window...")
window = Window(model, defaults)
window.Show()
app.SetTopWindow(window)
window.update_at_launch()
print("Starting main loop...")
exit_code = app.MainLoop()
print("...Main loop ended.")
print("Saving defaults...")

try:
    print("Saving defaults...")
    with open(defaults_file, 'w') as f:
        json.dump(defaults, f, indent=4)
    print("Defaults saved.")
except Exception as e:
    print(f"Error saving defaults: {e}")


try:
    print("Saving library...")
    with open(library_file, 'w') as f:
        json.dump(library, f, indent=4)
    print("Library saved.")
except Exception as e:
    print(f"Error saving library: {e}")

print("Exiting...")
sys.exit(exit_code)




