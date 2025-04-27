import wx
import wx.grid
import json
import os
from skein import Skein


class ColorDisplayPanel(wx.Panel):
    def __init__(self, parent, skein):
        super().__init__(parent, size=wx.Size(100, 50))
        self.skein = skein
        self.SetMinSize(wx.Size(100, 50))
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        dc = wx.PaintDC(self)

        # Get the size of the panel
        width, height = self.GetSize()

        # Draw background
        # dc.SetBrush(wx.Brush(wx.Colour(64, 64, 64)))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, 0, width, height)

        # Draw border
        dc.DrawRectangle(0, 0, width, height)

        # Draw color bands
        colors = self.skein.color
        if not colors:
            colors = [[200, 200, 200]]  # Default gray if no color

        num_colors = len(colors)
        if num_colors == 1:
            # Single color - fill the whole area
            r, g, b = colors[0]
            dc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
            dc.DrawRectangle(0, 0, width, height)
        else:
            # Multiple colors - draw horizontal bands
            band_width = width / num_colors
            for i, color in enumerate(colors):
                r, g, b = color
                dc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
                dc.DrawRectangle(int(i * band_width), 0, int(band_width), height)


class SkeinPanel(wx.Panel):
    def __init__(self, parent, skein, count=0, callback=None):
        super().__init__(parent, size=wx.Size(100, 100))
        self.skein = skein
        self.count = count
        self.brand = skein.brand
        self.sku = skein.sku
        self.callback = callback
        self.SetMinSize(wx.Size(100, 100))
        self.SetMaxSize(wx.Size(-1, 100))

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Add text in a dedicated area above the color panel
        text = f"{self.skein.brand.upper()}\n{self.skein.sku}\n{self.skein.name}"
        self.text_label = wx.StaticText(self, label=text, style=wx.ALIGN_CENTER)
        self.text_label.SetForegroundColour(wx.BLACK)
        font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.text_label.SetFont(font)

        sizer.Add(self.text_label, 0, wx.ALIGN_CENTER | wx.TOP, 5)

        # Add color display panel
        self.color_panel = ColorDisplayPanel(self, skein)
        sizer.Add(self.color_panel, 1, wx.EXPAND | wx.ALL, 5)

        # Add spinbox at the bottom
        spinbox_sizer = wx.BoxSizer()

        self.minus_button = wx.Button(self, label="-", size=wx.Size(35, 20))
        self.minus_button.Bind(wx.EVT_BUTTON, self._decrease_value)

        self.value_text = wx.TextCtrl(self, value=str(count), size=wx.Size(70, 20), style=wx.TE_CENTER)
        self.value_text.Bind(wx.EVT_TEXT, self._set_value)

        self.plus_button = wx.Button(self, label="+", size=wx.Size(35, 20))
        self.plus_button.Bind(wx.EVT_BUTTON, self._increase_value)

        spinbox_sizer.Add(self.minus_button, 0, wx.ALIGN_CENTER)
        spinbox_sizer.Add(self.value_text, 0, wx.ALIGN_CENTER)
        spinbox_sizer.Add(self.plus_button, 0, wx.ALIGN_CENTER)

        sizer.Add(spinbox_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)

        self.SetSizer(sizer)

    def _decrease_value(self, event):
        current = int(self.value_text.GetValue())
        if current > 0:
            new_value = current - 1
            self.value_text.SetValue(str(new_value))
            self.count = new_value
            if self.callback:
                self.callback(self.brand, self.sku, new_value)

    def _increase_value(self, event):
        current = int(self.value_text.GetValue())
        if current < 999:
            new_value = current + 1
            self.value_text.SetValue(str(new_value))
            self.count = new_value
            if self.callback:
                self.callback(self.brand, self.sku, new_value)

    def _set_value(self, event):
        new_value = int(self.value_text.GetValue())
        self.count = new_value
        if self.callback:
            self.callback(self.brand, self.sku, new_value)


class ColorPanel(wx.Panel):
    def __init__(self, parent, color: wx.Colour):
        super().__init__(parent, size=wx.Size(50, 50))
        self.color = list(wx.Colour(color).Get())
        self.SetMinSize(wx.Size(50, 50))
        self.SetMaxSize(wx.Size(50, 50))

        # Bind events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        # Get the size of the panel
        width, height = self.GetSize()

        # Draw border
        dc.SetPen(wx.Pen(wx.BLACK, 0))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(0, 0, width, height)

        # Fill with color
        dc.SetBrush(wx.Brush(wx.Colour(*self.color)))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(1, 1, width-2, height-2)

    def on_click(self, event):
        color_data = wx.ColourData()
        color_data.SetColour(wx.Colour(*self.color))
        dlg = wx.ColourDialog(self, color_data)

        if dlg.ShowModal() == wx.ID_OK:
            self.color = list(dlg.GetColourData().GetColour().Get())
            self.Refresh()

        dlg.Destroy()


class AddSkeinDialog(wx.Dialog):
    def __init__(self, parent, catalog):
        super().__init__(parent, title="Add New Skein")
        self.color_panels: list[ColorPanel] = []
        self.catalog = catalog

        # Create the main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Brand input
        brand_sizer = wx.BoxSizer()
        brand_label = wx.StaticText(self, label="Brand:\t")
        self.brand_input = wx.TextCtrl(self)
        brand_sizer.Add(brand_label, 0, wx.ALIGN_CENTER_VERTICAL)
        brand_sizer.Add(self.brand_input, 1, wx.EXPAND)
        main_sizer.Add(brand_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # SKU input
        sku_sizer = wx.BoxSizer()
        sku_label = wx.StaticText(self, label="SKU:\t")
        self.sku_input = wx.TextCtrl(self)
        sku_sizer.Add(sku_label, 0, wx.ALIGN_CENTER_VERTICAL)
        sku_sizer.Add(self.sku_input, 1, wx.EXPAND)
        main_sizer.Add(sku_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Name input
        name_sizer = wx.BoxSizer()
        name_label = wx.StaticText(self, label="Name:\t")
        self.name_input = wx.TextCtrl(self)
        name_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        name_sizer.Add(self.name_input, 1, wx.EXPAND)
        main_sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Colors section
        colors_sizer = wx.BoxSizer(wx.VERTICAL)
        colors_label = wx.StaticText(self, label="Colours:")
        colors_sizer.Add(colors_label, 0, wx.ALL, 5)

        # Color panels container
        self.colors_panel = wx.Panel(self)
        self.colors_sizer = wx.BoxSizer()
        self.colors_panel.SetSizer(self.colors_sizer)

        # Add initial color panel
        self.add_color(wx.WHITE)

        colors_sizer.Add(self.colors_panel, 0, wx.EXPAND | wx.ALL, 5)

        # Add/Remove color buttons
        color_buttons_sizer = wx.BoxSizer()
        add_color_button = wx.Button(self, label="Add Color")
        add_color_button.Bind(wx.EVT_BUTTON, self.add_color)
        remove_color_button = wx.Button(self, label="Remove Color")
        remove_color_button.Bind(wx.EVT_BUTTON, self.remove_color)
        color_buttons_sizer.Add(add_color_button, 0, wx.EXPAND | wx.ALL, 5)
        color_buttons_sizer.Add(remove_color_button, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(color_buttons_sizer, 0, wx.EXPAND, 5)
        main_sizer.Add(colors_sizer, 0, wx.EXPAND, 5)

        # Buttons
        button_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(self, wx.ID_OK)
        cancel_button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()

        main_sizer.Add(button_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(main_sizer)
        main_sizer.SetMinSize(wx.Size(400, 300))
        main_sizer.Fit(self)

    def add_color(self, event):
        color_panel = ColorPanel(self.colors_panel, wx.WHITE)
        self.color_panels.append(color_panel)
        self.colors_sizer.Add(color_panel, 0, wx.RIGHT, 5)
        self.colors_panel.Layout()

    def remove_color(self, event):
        if len(self.color_panels) > 1:
            # Remove the last color panel
            self.color_panels.pop().Destroy()
            self.colors_panel.Layout()

    def save_skein(self):
        colors = []
        for color_panel in self.color_panels:
            selected_color: list = color_panel.color
            colors.append([selected_color[0], selected_color[1], selected_color[2]])

        data = {
            "brand": self.brand_input.GetValue(),
            "sku": self.sku_input.GetValue(),
            "name": self.name_input.GetValue(),
            "color": colors
        }

        brand = data["brand"]
        sku = data["sku"]

        if not brand or not sku:
            wx.MessageBox("Brand and SKU are required.", "Input Error", wx.OK | wx.ICON_WARNING)
            return False

        # Create or update brand file
        brand_file = os.path.join("catalogs", f"{brand}.json")
        brand_data = {}

        # Load existing brand data if file exists
        if os.path.exists(brand_file):
            try:
                with open(brand_file, 'r') as f:
                    brand_data = json.load(f)
            except Exception as e:
                wx.MessageBox(f"Error loading brand file: {e}", "Error", wx.OK | wx.ICON_ERROR)
                return False

        # Add or update skein data
        brand_data[sku] = {
            "name": data["name"],
            "color": data["color"]
        }

        # Save brand file
        try:
            with open(brand_file, 'w') as f:
                json.dump(brand_data, f, indent=4)
        except Exception as e:
            wx.MessageBox(f"Error saving brand file: {e}", "Error", wx.OK | wx.ICON_ERROR)
            return False

        # Add to catalog
        if brand not in self.catalog.skeins:
            self.catalog.skeins[brand] = {}

        skein = Skein(brand, sku)
        skein.name = data["name"]
        skein.color = data["color"]
        self.catalog.skeins[brand][sku] = skein

        return True


class Window(wx.Frame):
    def __init__(self, library, catalog, parent=None):
        super().__init__(parent, title="Skein Care", size=wx.Size(800, 600))
        self.visible_skeins = None
        self.library = library
        self.catalog = catalog
        self.show_all = True  # Default to showing all skeins
        self.search_text = ""  # Initialize empty search text
        self.sort_method = 3  # Default sort by count

        # Create the main panel and sizer
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create a menu bar
        menubar = wx.MenuBar()
        file_menu = wx.Menu()

        # Add "Add New Skein" menu item
        add_skein_item = file_menu.Append(wx.ID_ANY, "Add New Skein")
        self.Bind(wx.EVT_MENU, self.add_skein, add_skein_item)

        # Add separator
        file_menu.AppendSeparator()

        # Add toggle for showing/hiding skeins not in library
        self.toggle_item = file_menu.AppendCheckItem(wx.ID_ANY, "Show All Skeins")
        self.toggle_item.Check(True)
        self.Bind(wx.EVT_MENU, self.toggle_skeins_visibility, self.toggle_item)

        menubar.Append(file_menu, "&File")

        sort_menu = wx.Menu()
        sort_by_brand_item = sort_menu.Append(0, "Brand")
        sort_by_sku_item = sort_menu.Append(1, "SKU")
        sort_by_name_item = sort_menu.Append(2, "Name")
        sort_by_count = sort_menu.Append(3, "Count")

        self.Bind(wx.EVT_MENU, self.sort_skeins, sort_by_brand_item)
        self.Bind(wx.EVT_MENU, self.sort_skeins, sort_by_sku_item)
        self.Bind(wx.EVT_MENU, self.sort_skeins, sort_by_name_item)
        self.Bind(wx.EVT_MENU, self.sort_skeins, sort_by_count)

        menubar.Append(sort_menu, "&Sort")

        self.SetMenuBar(menubar)

        self.search_bar = wx.SearchCtrl(self.panel)
        self.search_bar.SetHint("Search by SKU or name...")
        self.search_bar.Bind(wx.EVT_SEARCH, self.search)
        main_sizer.Add(self.search_bar, 0, wx.EXPAND | wx.ALL, 10)

        # Create scroll area for skeins grid
        self.scroll = wx.ScrolledWindow(self.panel)
        self.scroll.SetScrollRate(10, 10)

        # Create grid sizer for skeins
        self.grid_sizer = wx.GridSizer(rows=0, cols=5, hgap=10, vgap=10)

        # Set up the scroll area
        self.scroll.SetSizer(self.grid_sizer)
        main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(main_sizer)

        self.collect_visible_skeins()
        self.populate_grid()

        # Hack to refresh layout
        self.SetSize(wx.Size(self.GetSize()[0], self.GetSize()[1] + 1))

    def populate_grid(self):
        # Clear existing widgets
        self.grid_sizer.Clear(True)

        if self.sort_method == 0:  # Sort by brand
            self.visible_skeins.sort(key=lambda x: x[0].lower())  # Sort by brand (case-insensitive)
        elif self.sort_method == 1:  # Sort by SKU
            self.visible_skeins.sort(key=lambda x: int(x[1]) if x[1].isdecimal() else -1)  # Sort by SKU (case-insensitive)
        elif self.sort_method == 2:  # Sort by name
            self.visible_skeins.sort(key=lambda x: x[2].name.lower())  # Sort by name (case-insensitive)
        elif self.sort_method == 3:  # Sort by count
            self.visible_skeins.sort(key=lambda x: x[3], reverse=True)  # Sort by count (descending)

        # Freeze the window to prevent flickering
        self.scroll.Freeze()

        # Add sorted skeins to the grid
        for brand, sku, skein, count in self.visible_skeins:
            # Create skein panel with callback
            skein_panel = SkeinPanel(self.scroll, skein, count, callback=self.update_skein_count)

            # Add to grid
            self.grid_sizer.Add(skein_panel, 0, wx.EXPAND)

        # Update layout
        self.grid_sizer.Layout()
        self.scroll.FitInside()

        # Thaw the window to allow updates
        self.scroll.Thaw()

    def collect_visible_skeins(self):
        # Collect all visible skeins
        self.visible_skeins = []
        for brand, brand_skeins in self.catalog.skeins.items():
            for sku, skein in brand_skeins.items():
                # Check if we should show this skein
                count = 0
                if brand in self.library and sku in self.library[brand]:
                    count = self.library[brand][sku]

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

    def sort_skeins(self, event):
        id = event.GetId()
        # Brand, Sku, Name, Count

        if id == 0:
            self.sort_method = 0  # Sort by brand
        elif id == 1:
            self.sort_method = 1  # Sort by SKU
        elif id == 2:
            self.sort_method = 2  # Sort by name
        elif id == 3:
            self.sort_method = 3  # Sort by count
        else:
            raise ValueError("Invalid sort id.")

        self.populate_grid()

    def toggle_skeins_visibility(self, event):
        self.show_all = event.IsChecked()
        if self.show_all:
            self.toggle_item.SetItemLabel("Show All Skeins")
        else:
            self.toggle_item.SetItemLabel("Show Library Only")
        self.collect_visible_skeins()
        self.populate_grid()

    def search(self, event):
        self.search_text = event.GetString()
        self.populate_grid()

    def add_skein(self, event):
        dialog = AddSkeinDialog(self, self.catalog)
        if dialog.ShowModal() == wx.ID_OK:
            if dialog.save_skein():
                wx.MessageBox("Skein added successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.collect_visible_skeins()
                self.populate_grid()
        dialog.Destroy()

    def update_skein_count(self, brand, sku, count):
        if brand not in self.library:
            self.library[brand] = {}
        self.library[brand][sku] = count
