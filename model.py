import json
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
