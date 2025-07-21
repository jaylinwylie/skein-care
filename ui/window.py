import wx
import wx.grid
import wx.adv
import json
import os

import updater
from skein import Skein
from ui.panel import ColorPanel, SkeinPanel


class AddSkeinDialog(wx.Dialog):
    def __init__(self, parent, model):
        super().__init__(parent, title="Add New Skein")
        self.color_panels: list[ColorPanel] = []
        self.model = model

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

        main_sizer.Add(wx.StaticText(self, label='Click and drag to sample color from screen'))
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
            "brand": self.brand_input.GetValue().lower(),
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
        if brand not in self.model.catalog.skeins:
            self.model.catalog.skeins[brand] = {}

        skein = Skein(brand, sku)
        skein.name = data["name"]
        skein.color = data["color"]
        self.model.add_skein_to_catalog(skein)

        return True


class Window(wx.Frame):
    def __init__(self, skein_model, defaults: dict = None):
        self.skein_panels = {}
        import model
        super().__init__(parent=None, title="Skein Care", size=wx.Size(*(defaults.get('window_size', (800, 600)))))

        self.model: model.SkeinModel = skein_model
        self.model.sort_method = defaults.get('sort_method', 3)
        self.defaults = defaults

        self.SetPosition(wx.Point(*(defaults.get('window_position', (400, 300)))))
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        add_skein_item = file_menu.Append(wx.ID_ANY, "Add New Skein")
        self.Bind(wx.EVT_MENU, self.add_skein, add_skein_item)
        file_menu.AppendSeparator()

        self.toggle_item = file_menu.AppendCheckItem(wx.ID_ANY, "Show All Skeins")
        self.toggle_item.Check(True)
        self.Bind(wx.EVT_MENU, self.toggle_skeins_visibility, self.toggle_item)

        menubar.Append(file_menu, "&File")

        self.sort_menu = wx.Menu()
        self.sort_by_brand_item = self.sort_menu.AppendCheckItem(0, "Brand")
        self.sort_by_sku_item = self.sort_menu.AppendCheckItem(1, "SKU")
        self.sort_by_name_item = self.sort_menu.AppendCheckItem(2, "Name")
        self.sort_by_count_item = self.sort_menu.AppendCheckItem(3, "Count")

        if self.model.sort_method == 0:
            self.sort_by_brand_item.Check()
        elif self.model.sort_method == 1:
            self.sort_by_sku_item.Check()
        elif self.model.sort_method == 2:
            self.sort_by_name_item.Check()
        else:
            self.sort_by_count_item.Check()


        self.Bind(wx.EVT_MENU, self.sort_skeins, self.sort_by_brand_item)
        self.Bind(wx.EVT_MENU, self.sort_skeins, self.sort_by_sku_item)
        self.Bind(wx.EVT_MENU, self.sort_skeins, self.sort_by_name_item)
        self.Bind(wx.EVT_MENU, self.sort_skeins, self.sort_by_count_item)

        SkeinPanel.COUNT_CHANGE = self.update_skein_count
        SkeinPanel.EDIT_SKEIN = self.edit_skein

        menubar.Append(self.sort_menu, "&Sort")

        # Add Help menu with About item and Check for Updates
        help_menu = wx.Menu()
        check_updates_item = help_menu.Append(wx.ID_ANY, "Check for &Updates")
        self.Bind(wx.EVT_MENU, self.on_check_updates, check_updates_item)
        readme_item = help_menu.Append(wx.ID_ANY, "&Docs")
        self.Bind(wx.EVT_MENU, self.on_readme, readme_item)
        about_item = help_menu.Append(wx.ID_ABOUT, "&About")
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)
        self.CreateStatusBar()
        # Add skein counter above search bar
        self.skein_counter = wx.StaticText(self.panel, label="")
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.skein_counter.SetFont(font)
        main_sizer.Add(self.skein_counter, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 20)

        self.search_bar = wx.SearchCtrl(self.panel)
        self.search_bar.ShowCancelButton(True)
        self.search_bar.ShowSearchButton(True)
        self.search_bar.SetHint("Search by SKU or name...")
        self.search_bar.Bind(wx.EVT_SEARCH, self.search)
        self.search_bar.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.search)

        main_sizer.Add(self.search_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

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
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.update_panel_visibility()
        self.populate_grid()
        # Hack to refresh layout
        # self.SetSize(wx.Size(self.GetSize()[0] + 100, self.GetSize()[1] + 1))
        self._trigger_layout()

    def _trigger_layout(self):
        start_size = self.GetSize()
        self.SetSize(wx.Size(start_size[0], start_size[1] + 1))
        self.SetSize(start_size)
        self.SetMinSize(wx.Size(400, 400))

    @staticmethod
    def get_sort_option(sort_menu: wx.Menu) -> int:
        for menu_item in sort_menu.GetMenuItems():
            if menu_item.IsChecked():
                return menu_item.GetId()
        return -1

    def populate_grid(self):
        # Get visible panels
        panel_list = [(key, panel) for key, panel in self.skein_panels.items()]
        # Sort the panels based on the sort method
        sort_id = self.get_sort_option(self.sort_menu)
        if sort_id == 0:  # Sort by brand
            panel_list.sort(key=lambda x: x[1].brand.lower())
        elif sort_id == 1:  # Sort by SKU
            panel_list.sort(key=lambda x: int(x[1].sku) if x[1].sku.isdecimal() else -1)
        elif sort_id == 2:  # Sort by name
            panel_list.sort(key=lambda x: x[1].skein.name.lower())
        elif sort_id == 3:  # Sort by count
            panel_list.sort(key=lambda x: x[1].count, reverse=True)

        # Freeze the window to prevent flickering
        self.scroll.Freeze()

        # Clear the grid without destroying children
        self.grid_sizer.Clear(False)

        # Add panels to the grid in the sorted order
        for _, panel in panel_list:
            # Add to grid with spacing
            self.grid_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 5)

        # Update layout
        self.grid_sizer.Layout()
        self.scroll.FitInside()

        # Thaw the window to allow updates
        self.scroll.Thaw()

    def clear_grid(self):
        self.grid_sizer.Clear(True)
        self.skein_panels.clear()

    def update_panel_visibility(self):
        # Variables to track skein counts
        total_skeins = 0
        unique_skeins = 0

        is_show_all_skeins = self.toggle_item.IsChecked()
        search_text = self.search_bar.GetValue().lower()
        for brand, brand_skeins in self.model.catalog.skeins.items():
            for sku, skein in brand_skeins.items():
                count = 0
                if brand in self.model.library and sku in self.model.library[brand]:
                    count = self.model.library[brand][sku]

                total_skeins += count
                unique_skeins += 1

                if (brand, sku) not in self.skein_panels:
                    self.skein_panels[(brand, sku)] = SkeinPanel(self.scroll, skein, count)

                panel = self.skein_panels[(brand, sku)]
                if panel.count != count:
                    panel.count = count
                    panel.value_text.SetValue(str(count))

                if (not is_show_all_skeins and panel.count == 0) or (search_text and not (search_text in sku.lower() or search_text in skein.name.lower())):
                    panel.Hide()
                else:
                    panel.Show()

        # Update the skein counter text
        counter_text = f"Total Skeins: {total_skeins} | Unique Skeins: {unique_skeins}"
        self.skein_counter.SetLabel(counter_text)

    def sort_skeins(self, event):
        id = event.GetId()
        # Brand, Sku, Name, Count

        # Uncheck all sort menu items
        self.sort_by_brand_item.Check(False)
        self.sort_by_sku_item.Check(False)
        self.sort_by_name_item.Check(False)
        self.sort_by_count_item.Check(False)

        if id == 0:
            sort_method = 0  # Sort by brand
            self.sort_by_brand_item.Check(True)
        elif id == 1:
            sort_method = 1  # Sort by SKU
            self.sort_by_sku_item.Check(True)
        elif id == 2:
            sort_method = 2  # Sort by name
            self.sort_by_name_item.Check(True)
        elif id == 3:
            sort_method = 3  # Sort by count
            self.sort_by_count_item.Check(True)
        else:
            raise ValueError("Invalid sort id.")


        self.populate_grid()

    def toggle_skeins_visibility(self, event):
        show_all = event.IsChecked()
        if show_all:
            self.toggle_item.SetItemLabel("Show All Skeins")
        else:
            self.toggle_item.SetItemLabel("Show Library Only")
        self.update_panel_visibility()
        self.populate_grid()

    def search(self, event):
        # search_text = event.GetString()
        # if not search_text:
            # self.search_bar.SetValue('')
        self.update_panel_visibility()
        self.populate_grid()

    def add_skein(self, event):
        dialog = AddSkeinDialog(self, self.model)
        if dialog.ShowModal() == wx.ID_OK:
            if dialog.save_skein():
                wx.MessageBox("Skein added successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.update_panel_visibility()
                self.populate_grid()
        dialog.Destroy()

    def edit_skein(self, skein: Skein):
        dialog = AddSkeinDialog(self, self.model)
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

                if (skein.brand, skein.sku) in self.skein_panels:
                    self.skein_panels[(skein.brand, skein.sku)].Destroy()
                    del self.skein_panels[(skein.brand, skein.sku)]

                self.populate_grid()
                self.update_panel_visibility()
                self.populate_grid()

        dialog.Destroy()

    def update_skein_count(self, brand, sku, count):
        print(f"Updated skein count for {brand} - {sku} to {count}")
        self.SetStatusText(f"Updated skein count for {brand} - {sku} to {count}")
        # Update the count in the model
        self.model.update_skein_count(brand, sku, count)
        # Update the skein counter to reflect the new count
        self.update_panel_visibility()

    def on_resize(self, event):
        # Allow the event to propagate
        event.Skip()

        # Recalculate the layout
        self.grid_sizer.Layout()
        self.scroll.FitInside()

    def on_check_updates(self, event):
        """Check for updates and display the result to the user."""
        try:
            # Show a "checking for updates" message
            self.SetStatusText("Checking for updates...")
            current = updater.VERSION
            latest = updater.query_latest(updater.USER, updater.REPO)["tag_name"]
            print(f"Current version: {current}\nLatest version: {latest}")
            if latest:
                if updater.is_newer_version(updater.to_version(current), updater.to_version(latest)):
                    dialog = wx.adv.AboutDialogInfo()
                    dialog.SetName("Update")
                    dialog.SetDescription(f"A new update is available!\n{current} -> {latest}")
                    dialog.SetWebSite(updater.DOWNLOAD_LINK)
                    wx.adv.AboutBox(dialog)
                else:
                    wx.MessageBox(f"You have the latest version.\n{current}", "Update Check", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Error checking for updates: {e}", "Error", wx.OK | wx.ICON_ERROR)

        finally:
            self.SetStatusText("")

    def on_about(self, event):
        """Display the about dialog when the About menu item is clicked."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("Skein Care")
        info.SetDescription("Made by Jaylin Wylie Mayes - 2025\n\t- For my wife <3\n")
        info.SetWebSite(updater.DOWNLOAD_LINK)
        wx.adv.AboutBox(info)

    def on_readme(self, event):
        dialog = wx.Dialog(self, title="Documentation", size=(800, 500))
        sizer = wx.BoxSizer(wx.VERTICAL)
        text_ctrl = wx.TextCtrl(dialog, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        text_ctrl.SetValue(DOCS)
        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        text_ctrl.SetFont(font)
        sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        dialog.SetSizer(sizer)
        dialog.ShowModal()
        dialog.Destroy()


    def on_close(self, event):
        self.defaults.update({
                "window_size": (self.GetSize().x, self.GetSize().y),
                "window_position": (self.GetPosition().x, self.GetPosition().y),
                "sort_method": self.get_sort_option(self.sort_menu)
        })
        event.Skip()


DOCS = """\
Skein Care is a native desktop application designed to help catalog thread skeins for embroidery, cross-stitch, and other fiber arts.

- Each skein has a counter that you can adjust using the + and - buttons, or by entering a value directly.
- Sort collection by Brand, SKU, Name, or Count using the Sort menu.
- Use the search bar to quickly find skeins by SKU or name.

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
"""