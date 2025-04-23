import sys
import os
import json
from PySide6.QtWidgets import QApplication

from skein import Skein, Catalog
from ui import Window


class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.library: dict[str, dict[str, int]] = {}
        self.catalog = Catalog()

        self.load_catalogs()
        self.load_library()

        self.window = Window(self.library, self.catalog)
        self.window.show()

    def load_catalogs(self):
        """Load all available catalogs from the catalogs directory"""
        catalogs_dir = "catalogs"
        if not os.path.exists(catalogs_dir):
            os.makedirs(catalogs_dir)

        for filename in os.listdir(catalogs_dir):
            if filename.endswith(".json") and not filename.startswith("_"):
                brand = os.path.splitext(filename)[0]
                try:
                    data = {}
                    with open(os.path.join(catalogs_dir, filename)) as f:
                        data = json.load(f)
                    self.catalog.load_brand(brand, data)
                except Exception as e:
                    print(f"Error loading catalog {filename}: {e}")

    def load_library(self):
        """Load user's library data if it exists"""
        library_file = "library.json"
        if os.path.exists(library_file):
            try:
                with open(library_file, 'r') as f:
                    self.library = json.load(f)
            except Exception as e:
                print(f"Error loading library: {e}")

    def save_library(self):
        library_file = "library.json"
        try:
            with open(library_file, 'w') as f:
                json.dump(self.library, f, indent=4)
        except Exception as e:
            print(f"Error saving library: {e}")

    def run(self):
        """Run the application"""
        exit_code = self.app.exec()
        self.save_library()
        return exit_code








if __name__ == "__main__":
    app = Application()
    sys.exit(app.run())
