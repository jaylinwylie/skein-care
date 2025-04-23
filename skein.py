class Skein:    
    def __init__(self, brand: str, sku: str):
        self.brand = brand
        self.sku = sku
        self.name: str = 'no name'
        self.color: list[list[int]] = [[0, 0, 0]]
        self.material: str = 'cotton'


class Catalog:
    def __init__(self):
        self.skeins: dict[str, dict[str, Skein]] = {}

    def load_brand(self, brand: str, data: dict):
        if brand not in self.skeins:
            self.skeins[brand] = {}
        for sku, details in data.items():
            skein = Skein(brand, sku)
            skein.name = details.get('name', 'no name')
            skein.color = details.get('color', [[255, 255, 255]])
            skein.material = details.get('material', 'cotton')
            self.skeins[brand][sku] = skein
