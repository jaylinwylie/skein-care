import json
import os

import wx

from skein import Skein
from .panel import ColorPanel, SkeinPanel


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
        self.skein_panels = {}
        self.library = library
        self.catalog = catalog
        self.show_all = True
        self.search_text = ""
        self.sort_method = 3

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

        SkeinPanel.COUNT_CHANGE = self.update_skein_count
        SkeinPanel.EDIT_SKEIN = self.edit_skein

        menubar.Append(sort_menu, "&Sort")

        self.SetMenuBar(menubar)

        # Add skein counter above search bar
        self.skein_counter = wx.StaticText(self.panel, label="")
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.skein_counter.SetFont(font)
        main_sizer.Add(self.skein_counter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        self.search_bar = wx.SearchCtrl(self.panel)
        self.search_bar.ShowCancelButton(True)
        self.search_bar.ShowSearchButton(True)
        self.search_bar.SetHint("Search by SKU or name...")
        self.search_bar.Bind(wx.EVT_SEARCH, self.search)
        self.search_bar.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.search)

        main_sizer.Add(self.search_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Create scroll area for skeins grid
        self.scroll = wx.ScrolledWindow(self.panel)
        self.scroll.SetScrollRate(100, 100)

        # Create wrap sizer for dynamic tiling of skeins
        self.grid_sizer = wx.WrapSizer(wx.HORIZONTAL)

        # Set up the scroll area
        self.scroll.SetSizer(self.grid_sizer)
        main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(main_sizer)

        # Bind resize event
        self.Bind(wx.EVT_SIZE, self.on_resize)

        self.update_panel_visibility()
        self.populate_grid()

        # Hack to refresh layout
        self.SetSize(wx.Size(self.GetSize()[0] + 60, self.GetSize()[1] + 1))
        # Allow horizontal resizing by setting only minimum height
        self.SetMinSize(wx.Size(860, self.GetSize()[1]))
        # Allow horizontal resizing by setting only maximum height
        self.SetMaxSize(wx.Size(-1, self.GetSize()[1] + 1000))

    def populate_grid(self):
        # Get visible panels
        visible_panels = [(key, panel) for key, panel in self.skein_panels.items() if panel.visible]

        # Sort the panels based on the sort method
        if self.sort_method == 0:  # Sort by brand
            visible_panels.sort(key=lambda x: x[1].brand.lower())
        elif self.sort_method == 1:  # Sort by SKU
            visible_panels.sort(key=lambda x: int(x[1].sku) if x[1].sku.isdecimal() else -1)
        elif self.sort_method == 2:  # Sort by name
            visible_panels.sort(key=lambda x: x[1].skein.name.lower())
        elif self.sort_method == 3:  # Sort by count
            visible_panels.sort(key=lambda x: x[1].count, reverse=True)

        # Freeze the window to prevent flickering
        self.scroll.Freeze()

        # Clear the grid without destroying children
        self.grid_sizer.Clear(False)

        # Add panels to the grid in the sorted order
        for _, panel in visible_panels:
            # Add to grid with spacing
            self.grid_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 5)

        # Update layout
        self.grid_sizer.Layout()
        self.scroll.FitInside()

        # Thaw the window to allow updates
        self.scroll.Thaw()

    def update_panel_visibility(self):
        # Variables to track skein counts
        total_skeins = 0
        unique_skeins = 0

        # Track which panels should be visible
        visible_panels = set()

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

                # Determine if this skein should be visible
                visible = True

                # Apply filters
                if not self.show_all and count == 0:
                    visible = False  # Skip skeins not in library if toggle is off

                # Apply search filter
                if self.search_text and not (
                        self.search_text.lower() in sku.lower() or
                        self.search_text.lower() in skein.name.lower()
                ):
                    visible = False  # Skip if doesn't match search

                panel_key = (brand, sku)

                # Create panel if it doesn't exist yet
                if panel_key not in self.skein_panels:
                    self.skein_panels[panel_key] = SkeinPanel(self.scroll, skein, count)

                # Update count if needed
                panel = self.skein_panels[panel_key]
                if panel.count != count:
                    panel.count = count
                    panel.value_text.SetValue(str(count))

                # Show or hide panel based on visibility
                if visible:
                    visible_panels.add(panel_key)
                    panel.Show()
                    panel.visible = True
                else:
                    panel.Hide()
                    panel.visible = False

        # Update the skein counter text
        counter_text = f"Total Skeins: {total_skeins} | Unique Skeins: {unique_skeins}"
        self.skein_counter.SetLabel(counter_text)

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
        self.update_panel_visibility()
        self.populate_grid()

    def search(self, event):
        self.search_text = event.GetString()
        if not self.search_text:
            self.search_bar.SetValue('')
        self.update_panel_visibility()
        self.populate_grid()

    def add_skein(self, event):
        dialog = AddSkeinDialog(self, self.catalog)
        if dialog.ShowModal() == wx.ID_OK:
            if dialog.save_skein():
                wx.MessageBox("Skein added successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.update_panel_visibility()
                self.populate_grid()
        dialog.Destroy()

    def edit_skein(self, skein: Skein):
        dialog = AddSkeinDialog(self, self.catalog)
        dialog.brand_input.SetValue(skein.brand.upper())
        dialog.name_input.SetValue(skein.name)
        dialog.sku_input.SetValue(skein.sku)

        dialog.color_panels[0].color = skein.color[0]
        for color in skein.color[1:]:
            dialog.add_color(event=None)
            dialog.color_panels[-1].color = color

        if dialog.ShowModal() == wx.ID_OK:
            if dialog.save_skein():
                wx.MessageBox("Skein edited successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.update_panel_visibility()
                self.populate_grid()

        dialog.Destroy()

    def update_skein_count(self, brand, sku, count):
        if brand not in self.library:
            self.library[brand] = {}
        self.library[brand][sku] = count

        # Update the skein counter to reflect the new count
        self.update_panel_visibility()

    def on_resize(self, event):
        # dont layout is mouse button down
        self.grid_sizer.Layout()
        self.scroll.FitInside()
        event.Skip()
