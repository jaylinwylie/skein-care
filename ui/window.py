import wx
import wx.grid
import wx.adv
import json
import os
import webbrowser

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

        main_sizer.Add(wx.StaticText(self, label='Left-click and drag to sample color from screen, right-click to open color dialog' if 'wxMSW' in wx.PlatformInfo else "Click on a panel to edit its colour"))
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


class EditSkeinDialog(AddSkeinDialog):
    def __init__(self, parent, model, skein: Skein):
        super().__init__(parent, model)
        
        # Change the dialog title to reflect editing
        self.SetTitle(f"Edit Skein - {skein.brand} {skein.sku}")
        
        # Populate the fields with the existing skein data
        self.brand_input.SetValue(skein.brand.upper())
        self.name_input.SetValue(skein.name)
        self.sku_input.SetValue(skein.sku)
        
        self.sku_input.Enable(False)
        self.brand_input.Enable(False)

        # Set up the color panels
        self.color_panels[0].color = skein.color[0]
        for color in skein.color[1:]:
            self.add_color(event=None)
            self.color_panels[-1].color = color
        
        # Store the original skein for reference
        self.original_skein = skein
        
        # Add delete button
        button_sizer = self.GetSizer().GetItem(self.GetSizer().GetItemCount() - 1).GetSizer()
        self.delete_button = wx.Button(self, label="Delete Skein")
        button_sizer.Insert(0, self.delete_button, 0, wx.ALL, 5)
        
        # Bind delete button event
        self.delete_button.Bind(wx.EVT_BUTTON, self.on_delete)
        
        # Refresh layout
        self.Layout()
    
    def on_delete(self, event):
        # Show confirmation dialog
        brand = self.original_skein.brand
        sku = self.original_skein.sku
        name = self.original_skein.name
        
        message = f"Are you sure you want to delete this skein?\n\nBrand: {brand.upper()}\nSKU: {sku}\nName: {name}\n\nThis will permanently remove it from the catalog."
        dialog = wx.MessageDialog(self, message, "Confirm Delete", wx.YES_NO | wx.ICON_WARNING)
        
        if dialog.ShowModal() == wx.ID_YES:
            # Delete the skein
            if self.model.delete_skein(brand, sku):
                wx.MessageBox(f"Skein {brand.upper()} {sku} has been deleted.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.EndModal(wx.ID_CANCEL)  # Close the dialog
            else:
                wx.MessageBox("Failed to delete the skein.", "Error", wx.OK | wx.ICON_ERROR)
        
        dialog.Destroy()


class Window(wx.Frame):
    def __init__(self, skein_model, defaults: dict = None):
        self.skein_panels = {}
        import model
        super().__init__(parent=None, title="Skein Care", size=wx.Size(*(defaults.get('window_size', (875, 600)))))

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

        self.toggle_item = file_menu.AppendCheckItem(wx.ID_ANY, "Show Library Only")
        self.toggle_item.Check(True)
        self.Bind(wx.EVT_MENU, self.toggle_skeins_visibility, self.toggle_item)

        menubar.Append(file_menu, "&File")

        self.sort_menu = wx.Menu()
        # Define sort method constants
        self.SORT_BY_BRAND = 0
        self.SORT_BY_SKU = 1
        self.SORT_BY_NAME = 2
        self.SORT_BY_COUNT = 3

        # Create menu items with wx.ID_ANY and store their IDs
        self.sort_by_brand_item = self.sort_menu.AppendCheckItem(wx.ID_ANY, "Brand")
        self.sort_by_brand_id = self.sort_by_brand_item.GetId()

        self.sort_by_sku_item = self.sort_menu.AppendCheckItem(wx.ID_ANY, "SKU")
        self.sort_by_sku_id = self.sort_by_sku_item.GetId()

        self.sort_by_name_item = self.sort_menu.AppendCheckItem(wx.ID_ANY, "Name")
        self.sort_by_name_id = self.sort_by_name_item.GetId()

        self.sort_by_count_item = self.sort_menu.AppendCheckItem(wx.ID_ANY, "Count")
        self.sort_by_count_id = self.sort_by_count_item.GetId()

        if self.model.sort_method == self.SORT_BY_BRAND:
            self.sort_by_brand_item.Check()
        elif self.model.sort_method == self.SORT_BY_SKU:
            self.sort_by_sku_item.Check()
        elif self.model.sort_method == self.SORT_BY_NAME:
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
        if sort_id == self.sort_by_brand_id:  # Sort by brand
            panel_list.sort(key=lambda x: x[1].brand.lower())
        elif sort_id == self.sort_by_sku_id:  # Sort by SKU
            panel_list.sort(key=lambda x: int(x[1].sku) if x[1].sku.isdecimal() else -1)
        elif sort_id == self.sort_by_name_id:  # Sort by name
            panel_list.sort(key=lambda x: x[1].skein.name.lower())
        elif sort_id == self.sort_by_count_id:  # Sort by count
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

        is_show_all_skeins = not self.toggle_item.IsChecked()
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

        if id == self.sort_by_brand_id:
            self.model.sort_method = self.SORT_BY_BRAND  # Sort by brand
            self.sort_by_brand_item.Check(True)
        elif id == self.sort_by_sku_id:
            self.model.sort_method = self.SORT_BY_SKU  # Sort by SKU
            self.sort_by_sku_item.Check(True)
        elif id == self.sort_by_name_id:
            self.model.sort_method = self.SORT_BY_NAME  # Sort by name
            self.sort_by_name_item.Check(True)
        elif id == self.sort_by_count_id:
            self.model.sort_method = self.SORT_BY_COUNT  # Sort by count
            self.sort_by_count_item.Check(True)
        else:
            raise ValueError("Invalid sort id.")


        self.populate_grid()

    def toggle_skeins_visibility(self, event):
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
        """Edit a skein and return True if the skein was deleted, False otherwise."""
        dialog = EditSkeinDialog(self, self.model, skein)
        was_deleted = False

        result = dialog.ShowModal()
        if result == wx.ID_OK:
            if dialog.save_skein():
                wx.MessageBox("Skein edited successfully.", "Success", wx.OK | wx.ICON_INFORMATION)

                if (skein.brand, skein.sku) in self.skein_panels:
                    self.skein_panels[(skein.brand, skein.sku)].Destroy()
                    del self.skein_panels[(skein.brand, skein.sku)]

                self.populate_grid()
                self.update_panel_visibility()
                self.populate_grid()
        elif result == wx.ID_CANCEL:
            # Check if the skein was deleted (we need to update the UI)
            if skein.brand in self.model.catalog.skeins and skein.sku in self.model.catalog.skeins[skein.brand]:
                # Skein still exists, do nothing
                pass
            else:
                # Skein was deleted, update UI
                was_deleted = True
                if (skein.brand, skein.sku) in self.skein_panels:
                    self.skein_panels[(skein.brand, skein.sku)].Destroy()
                    del self.skein_panels[(skein.brand, skein.sku)]
                self.update_panel_visibility()
                self.populate_grid()

        dialog.Destroy()
        return was_deleted

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
            # Check if there is an update available
            status, latest = updater.query_latest(updater.USER, updater.REPO)
            if status:
                latest_tag = latest["tag_name"]
                body = latest["body"]
                link = updater.KO_FI_URL

                if updater.is_newer_version(updater.to_version(updater.VERSION), updater.to_version(latest_tag)):
                    dialog = wx.Dialog(self, title="Update Available", size=(300, 150))
                    sizer = wx.BoxSizer(wx.VERTICAL)
                    message = wx.StaticText(dialog, label=f"A new update is available!\n{updater.VERSION} -> {latest_tag}\n\n{body}")

                    sizer.Add(message, 0, wx.ALL | wx.CENTER, 10)
                    button_sizer = wx.BoxSizer(wx.HORIZONTAL)
                    release_button = wx.Button(dialog, label="Go to Release")

                    def on_release(event):
                        webbrowser.open(updater.KO_FI_URL)
                        dialog.EndModal(wx.ID_CANCEL)

                    release_button.Bind(wx.EVT_BUTTON, on_release)
                    button_sizer.Add(release_button, 0, wx.ALL, 5)
                    sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
                    dialog.SetSizer(sizer)
                    dialog.Fit()
                    dialog.ShowModal()
                    dialog.Destroy()

        except Exception as e:
            self.SetStatusText(f"Error checking for updates: {e}")


    def update_at_launch(self):
        """Update the application at launch."""
        try:
            # Check if there is an update available
            status, latest = updater.query_latest(updater.USER, updater.REPO)
            if status:
                latest_tag = latest["tag_name"]
                body = latest["body"]
                link = updater.KO_FI_URL
                
                # Check if this version is in the skip list
                skip_version = self.defaults.get('skip_version')
                if skip_version and skip_version == latest_tag:
                    # Skip this version as requested by the user
                    return

                if updater.is_newer_version(updater.to_version(updater.VERSION), updater.to_version(latest_tag)):
                    dialog = wx.Dialog(self, title="Update Available", size=(300, 150))
                    sizer = wx.BoxSizer(wx.VERTICAL)

                    # Message text
                    message = wx.StaticText(dialog, label=f"A new update is available!\n{updater.VERSION} -> {latest_tag}\n\n{body}")
                    sizer.Add(message, 0, wx.ALL | wx.CENTER, 10)

                    # Buttons
                    button_sizer = wx.BoxSizer(wx.HORIZONTAL)
                    skip_button = wx.Button(dialog, label="Skip Version")
                    ignore_button = wx.Button(dialog, label="Ignore")
                    release_button = wx.Button(dialog, label="Go to Release")

                    # Bind events to buttons
                    def on_skip(event):
                        # Add this version to the skip list
                        self.defaults['skip_version'] = latest_tag
                        dialog.EndModal(wx.ID_CANCEL)

                    def on_ignore(event):
                        # Just close the dialog
                        dialog.EndModal(wx.ID_CANCEL)

                    def on_release(event):
                        webbrowser.open(updater.KO_FI_URL)
                        dialog.EndModal(wx.ID_CANCEL)

                    skip_button.Bind(wx.EVT_BUTTON, on_skip)
                    ignore_button.Bind(wx.EVT_BUTTON, on_ignore)
                    release_button.Bind(wx.EVT_BUTTON, on_release)

                    button_sizer.Add(skip_button, 0, wx.ALL, 5)
                    button_sizer.Add(ignore_button, 0, wx.ALL, 5)
                    button_sizer.Add(release_button, 0, wx.ALL, 5)
                    sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)

                    dialog.SetSizer(sizer)
                    dialog.Fit()
                    dialog.ShowModal()
                    dialog.Destroy()

        except Exception as e:
            self.SetStatusText(f"Error checking for updates: {e}")

    def on_about(self, event):
        """Display the about dialog when the About menu item is clicked."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("Skein Care")
        info.SetVersion(updater.VERSION)
        info.SetDescription("~For my wife <3\n\n\n\n\n\nConsider Donating!")
        info.SetCopyright("(c) 2025 Jaylin Wylie Mayes")
        info.SetLicence(LICENCE)
        info.SetWebSite(updater.KO_FI_URL)
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
        # Convert the dynamic menu item ID to the constant sort method value
        sort_id = self.get_sort_option(self.sort_menu)
        sort_method = self.SORT_BY_COUNT  # Default to count
        if sort_id == self.sort_by_brand_id:
            sort_method = self.SORT_BY_BRAND
        elif sort_id == self.sort_by_sku_id:
            sort_method = self.SORT_BY_SKU
        elif sort_id == self.sort_by_name_id:
            sort_method = self.SORT_BY_NAME
        elif sort_id == self.sort_by_count_id:
            sort_method = self.SORT_BY_COUNT

        self.defaults.update({
                "window_size": (self.GetSize().x, self.GetSize().y),
                "window_position": (self.GetPosition().x, self.GetPosition().y),
                "sort_method": sort_method
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

### Data Management
- Click on any skein in your collection to edit its details
- Skein collection is saved in "library.json"
- Skein catalogs are stored in the "catalogs"
- User preferences are saved in "defaults.json"
"""

LICENCE = """\
MIT License

Copyright (c) 2025 Jaylin Wylie Mayes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
