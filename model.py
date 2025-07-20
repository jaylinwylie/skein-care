from skein import Skein, Catalog

class SkeinModel:
    def __init__(self, library, catalog):
        self.library = library
        self.catalog = catalog
        self.visible_skeins = []
        self.show_all = True  # Default to showing all skeins
        self.search_text = ""  # Initialize empty search text
        self.sort_method = 3  # Default sort by count
        self.collect_visible_skeins()

    def collect_visible_skeins(self):
        """Collect all visible skeins based on current filters and search"""
        # Collect all visible skeins
        self.visible_skeins = []

        # Variables to track skein counts
        total_skeins = 0
        unique_skeins = 0

        for brand, brand_skeins in self.catalog.skeins.items():
            for sku, skein in brand_skeins.items():
                # Check if we should show this skein
                count = 0
                if brand in self.library and sku in self.library[brand]:
                    count = self.library[brand][sku]

                # Count total skeins and unique skeins
                if count > 0:
                    total_skeins += count
                    unique_skeins += 1

                if not self.show_all and count == 0:
                    continue  # Skip skeins not in library if toggle is off

                # Check if skein matches search criteria
                if self.search_text and not (
                        self.search_text.lower() in sku.lower() or
                        self.search_text.lower() in skein.name.lower()
                ):
                    continue  # Skip if doesn't match search

                # Add to visible skeins
                self.visible_skeins.append((brand, sku, skein, count))

        return total_skeins, unique_skeins

    def update_skein_count(self, brand, sku, count):
        """Update the count of a skein in the library"""
        if brand not in self.library:
            self.library[brand] = {}
        self.library[brand][sku] = count
        # Update the visible skeins to reflect the new count
        self.collect_visible_skeins()

    def sort_visible_skeins(self):
        """Sort the visible skeins based on the current sort method"""
        if self.sort_method == 0:  # Sort by brand
            self.visible_skeins.sort(key=lambda x: x[0].lower())  # Sort by brand (case-insensitive)
        elif self.sort_method == 1:  # Sort by SKU
            self.visible_skeins.sort(key=lambda x: int(x[1]) if x[1].isdecimal() else -1)  # Sort by SKU (case-insensitive)
        elif self.sort_method == 2:  # Sort by name
            self.visible_skeins.sort(key=lambda x: x[2].name.lower())  # Sort by name (case-insensitive)
        elif self.sort_method == 3:  # Sort by count
            self.visible_skeins.sort(key=lambda x: x[3], reverse=True)  # Sort by count (descending)

    def set_sort_method(self, sort_method):
        """Set the sort method and re-sort the visible skeins"""
        self.sort_method = sort_method
        self.sort_visible_skeins()

    def toggle_skeins_visibility(self, show_all):
        """Toggle between showing all skeins or only those in the library"""
        self.show_all = show_all
        self.collect_visible_skeins()

    def search(self, search_text):
        """Filter skeins based on search text"""
        self.search_text = search_text
        self.collect_visible_skeins()

    def add_skein_to_catalog(self, skein):
        """Add a new skein to the catalog"""
        brand = skein.brand
        sku = skein.sku
        
        if brand not in self.catalog.skeins:
            self.catalog.skeins[brand] = {}
            
        self.catalog.skeins[brand][sku] = skein
        self.collect_visible_skeins()