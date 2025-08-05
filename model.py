import json
import os
from pathlib import Path
from skein import Skein, Catalog


def csv_to_json(csv_path: Path):
    csv_data: list = []
    with open(csv_path) as f:
        csv_data = f.readlines()

    json_data: dict = {}
    for line in csv_data:
        print(line)
        sku, name, r, g, b = line.strip().split(',')
        color = [int(r), int(g), int(b)]
        if sku not in json_data:
            skein = {'name': name.strip(), 'color': [color]}
            print(skein)
            json_data[sku] = skein

    json_filename = csv_path.stem.lower() + '.json'
    with open(csv_path.parent / json_filename, 'w') as f:
        f.write(json.dumps(json_data, indent=4))


class SkeinModel:
    def __init__(self, library, catalog):
        self.library = library
        self.catalog = catalog
        self.sort_method = 0  # Default sort by brand

    def update_skein_count(self, brand, sku, count):
        if brand not in self.library:
            self.library[brand] = {}
        self.library[brand][sku] = count

    def add_skein_to_catalog(self, skein):
        brand = skein.brand
        sku = skein.sku

        if brand not in self.catalog.skeins:
            self.catalog.skeins[brand] = {}

        self.catalog.skeins[brand][sku] = skein
        
    def delete_skein(self, brand, sku):
        """Delete a skein from both catalog and library"""
        # Remove from catalog if exists
        if brand in self.catalog.skeins and sku in self.catalog.skeins[brand]:
            del self.catalog.skeins[brand][sku]
            
            # If brand has no more skeins, remove the brand entry
            if not self.catalog.skeins[brand]:
                del self.catalog.skeins[brand]
                
            # Also remove from library if exists
            if brand in self.library and sku in self.library[brand]:
                del self.library[brand][sku]
                
                # If brand has no more skeins in library, remove the brand entry
                if not self.library[brand]:
                    del self.library[brand]
                    
            # Delete the skein from the brand file
            brand_file = f"catalogs/{brand}.json"
            if os.path.exists(brand_file):
                try:
                    with open(brand_file, 'r') as f:
                        brand_data = json.load(f)
                    
                    if sku in brand_data:
                        del brand_data[sku]
                        
                    with open(brand_file, 'w') as f:
                        json.dump(brand_data, f, indent=4)
                except Exception as e:
                    print(f"Error updating brand file: {e}")
                    
            return True
        return False
