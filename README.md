# Skein Care

A native desktop application designed to help catalog thread skeins for embroidery, cross-stitch, and other fiber arts.

## Features

- Track your thread inventory with adjustable counters
- Sort collection by Brand, SKU, Name, or Count
- Search skeins by SKU or name
- Pick colors directly from your screen

## Installation

1. Ensure you have Python installed
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

## Usage

### Adding New Skeins
1. Click on "File" > "Add New Skein"
2. Enter details:
   - Brand: The manufacturer of the skein
   - SKU: The product code/number
   - Name: The color name or description
   - Colors: Add one or more colors for the skein
3. Click "OK" to add the skein to your catalog

### Color Picking
1. Click and hold on a color square in the dialog
2. Your cursor will change to a crosshair
3. Drag over any area of your screen to sample
4. Release to set the color

### Data Management
- Click on any skein in your collection to edit its details
- Skein collection is saved in "library.json"
- Skein catalogs are stored in the "catalogs" folder as JSON files
- User preferences are saved in "defaults.json"
