import wx
import wx.grid
import json
import os
from skein import Skein
from model import SkeinModel


class ColorDisplayPanel(wx.Panel):
    def __init__(self, parent, skein):
        super().__init__(parent, size=wx.Size(100, 100))
        self.skein = skein
        self.SetMinSize(wx.Size(100, 400))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.average_lightness = self.calculate_average_lightness(self.skein.color)

    def on_paint(self, event):
        dc = wx.PaintDC(self)

        # Get the size of the panel
        width, height = self.GetSize()

        # Draw background
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
                dc.DrawRectangle(int(i * band_width), 0, int(band_width) + 1, height)

        # Create a transparent DC for drawing text
        gc = wx.GraphicsContext.Create(dc)
        if gc:
            # Calculate text color based on average lightness
            text_color = wx.BLACK if self.average_lightness > 0.5 else wx.WHITE

            # Set font and text color
            font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            gc.SetFont(font, text_color)

            # Get line height and handle multiline text for brand title
            brand_lines = self.skein.brand.upper().split()
            line_spacing = 2  # spacing between lines within the same text block
            title_height = 0
            max_title_width = 0
            for line in brand_lines:
                w, h = gc.GetTextExtent(line)
                title_height += h + line_spacing
                max_title_width = max(max_title_width, w)
            title_height -= line_spacing  # remove extra spacing after last line

            # Get dimensions for SKU
            sku_width, sku_height = gc.GetTextExtent(self.skein.sku)

            # Handle multiline name text
            name_lines = self.skein.name.split()
            name_height = 0
            max_name_width = 0
            for line in name_lines:
                w, h = gc.GetTextExtent(line)
                name_height += h + line_spacing
                max_name_width = max(max_name_width, w)
            name_height -= line_spacing  # remove extra spacing after last line

            # Calculate total text height including spacing between blocks
            block_spacing = 10  # pixels between different text blocks
            total_text_height = title_height + sku_height + name_height + (2 * block_spacing)

            # Calculate starting Y position to center all elements vertically
            start_y = (height - total_text_height) / 2

            # Draw brand title (multiline)
            current_y = start_y
            for line in brand_lines:
                w, h = gc.GetTextExtent(line)
                text_x = (width - w) / 2
                gc.DrawText(line, text_x, current_y)
                current_y += h + line_spacing

            # Draw SKU
            sku_x = (width - sku_width) / 2
            sku_y = start_y + title_height + block_spacing
            gc.DrawText(self.skein.sku, sku_x, sku_y)

            # Draw name (multiline)
            current_y = sku_y + sku_height + block_spacing
            for line in name_lines:
                w, h = gc.GetTextExtent(line)
                text_x = (width - w) / 2
                gc.DrawText(line, text_x, current_y)
                current_y += h + line_spacing

    @staticmethod
    def calculate_average_lightness(colors):
        """Calculate the average lightness of the colors"""
        if not colors:
            return 0.5  # Default middle lightness

        total_lightness = 0
        for color in colors:
            r, g, b = color
            lightness = wx.Colour(r, g, b).GetLuminance()
            total_lightness += lightness

        return total_lightness / len(colors)


class SkeinPanel(wx.Panel):
    EDIT_SKEIN = None
    COUNT_CHANGE = None

    def __init__(self, parent, skein, count=0):
        super().__init__(parent, size=wx.Size(150, 200))
        self.skein = skein
        self.count = count
        self.brand = skein.brand
        self.sku = skein.sku
        self.SetMinSize(wx.Size(150, 200))

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Add color display panel
        self.color_panel = ColorDisplayPanel(self, skein)
        self.color_panel.Bind(wx.EVT_LEFT_DOWN, self.on_click)
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

    def on_click(self, event):
        print(f"{self.skein.name} clicked")
        self.EDIT_SKEIN(self.skein)

    def _decrease_value(self, event):
        current = int(self.value_text.GetValue())
        if current > 0:
            new_value = current - 1
            self.value_text.SetValue(str(new_value))
            self.count = new_value
            if self.COUNT_CHANGE:
                self.COUNT_CHANGE(self.brand, self.sku, new_value)

    def _increase_value(self, event):
        current = int(self.value_text.GetValue())
        if current < 999:
            new_value = current + 1
            self.value_text.SetValue(str(new_value))
            self.count = new_value
            if self.COUNT_CHANGE:
                self.COUNT_CHANGE(self.brand, self.sku, new_value)

    def _set_value(self, event):
        new_value = int(self.value_text.GetValue())
        self.count = new_value
        if self.COUNT_CHANGE:
            self.COUNT_CHANGE(self.brand, self.sku, new_value)


class ColorPanel(wx.Panel):
    def __init__(self, parent, color: wx.Colour):
        super().__init__(parent, size=wx.Size(50, 50))
        self.color = list(wx.Colour(color).Get())
        self.SetMinSize(wx.Size(50, 50))
        self.SetMaxSize(wx.Size(50, 50))
        self.picking = False

        # Create timer for screen color sampling
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)

        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.start_picking)
        self.Bind(wx.EVT_LEFT_UP, self.stop_picking)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        width, height = self.GetSize()

        # Draw border
        dc.SetPen(wx.Pen(wx.BLACK, 0))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(0, 0, width, height)

        # Fill with color
        dc.SetBrush(wx.Brush(wx.Colour(*self.color)))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(1, 1, width - 2, height - 2)

    def start_picking(self, event):
        if not self.picking:
            self.picking = True
            self.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
            # Capture mouse and keyboard events globally
            self.CaptureMouse()
            self.Bind(wx.EVT_LEFT_DOWN, self.stop_picking)
            self.Bind(wx.EVT_RIGHT_DOWN, self.stop_picking)
            # Start timer for color sampling
            self.timer.Start(50)  # Update every 50ms

        event.Skip()

    def on_timer(self, event):
        if self.picking:
            # Get screen position
            x, y = wx.GetMousePosition()

            # Get color at current position
            dc = wx.ScreenDC()
            color = dc.GetPixel(x, y)

            # Update preview
            self.color = list(color.Get())
            self.Refresh()

    def stop_picking(self, event):
        if self.picking:
            self.picking = False
            self.SetCursor(wx.NullCursor)

            if self.HasCapture():
                self.ReleaseMouse()

            wx.GetTopLevelParent(self).Unbind(wx.EVT_KEY_DOWN)
            self.Unbind(wx.EVT_LEFT_DOWN)
            self.Unbind(wx.EVT_RIGHT_DOWN)

            self.timer.Stop()
        event.Skip()


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

        # Create skein and add to model
        skein = Skein(brand, sku)
        skein.name = data["name"]
        skein.color = data["color"]
        self.model.add_skein_to_catalog(skein)

        return True


class Window(wx.Frame):
    def __init__(self, model, defaults: dict = None):
        super().__init__(parent=None, title="Skein Care", size=wx.Size(*(defaults.get('window_size', (800, 600)))))
        self.model = model
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

        sort_menu = wx.Menu()
        self.sort_by_brand_item = sort_menu.AppendCheckItem(0, "Brand")
        self.sort_by_sku_item = sort_menu.AppendCheckItem(1, "SKU")
        self.sort_by_name_item = sort_menu.AppendCheckItem(2, "Name")
        self.sort_by_count_item = sort_menu.AppendCheckItem(3, "Count")

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

        menubar.Append(sort_menu, "&Sort")

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
        self.scroll.SetScrollRate(100, 200)

        # Create wrap sizer for dynamic tiling of skeins
        self.grid_sizer = wx.WrapSizer(wx.HORIZONTAL)

        # Set up the scroll area
        self.scroll.SetSizer(self.grid_sizer)
        main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(main_sizer)

        # Bind resize event
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.collect_visible_skeins()
        self.populate_grid()

        # Hack to refresh layout
        # self.SetSize(wx.Size(self.GetSize()[0] + 100, self.GetSize()[1] + 1))
        start_size = self.GetSize()
        self.SetSize((start_size[0], start_size[1] + 1))
        self.SetSize(start_size)
        self.SetMinSize(wx.Size(400, 400))

    def populate_grid(self):
        # Clear existing widgets
        self.grid_sizer.Clear(True)

        # Sort the visible skeins using the model
        self.model.sort_visible_skeins()

        # Freeze the window to prevent flickering
        self.scroll.Freeze()

        # Add sorted skeins to the grid
        for brand, sku, skein, count in self.model.visible_skeins:
            # Create skein panel with callback
            skein_panel = SkeinPanel(self.scroll, skein, count)

            # Add to grid with spacing
            self.grid_sizer.Add(skein_panel, 0, wx.EXPAND | wx.ALL, 5)

        # Update layout
        self.grid_sizer.Layout()
        self.scroll.FitInside()

        # Thaw the window to allow updates
        self.scroll.Thaw()

    def collect_visible_skeins(self):
        # Use the model to collect visible skeins
        total_skeins, unique_skeins = self.model.collect_visible_skeins()

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

        # Update the sort method in the model
        self.model.set_sort_method(sort_method)
        self.populate_grid()

    def toggle_skeins_visibility(self, event):
        show_all = event.IsChecked()
        if show_all:
            self.toggle_item.SetItemLabel("Show All Skeins")
        else:
            self.toggle_item.SetItemLabel("Show Library Only")
        # Update the visibility in the model
        self.model.toggle_skeins_visibility(show_all)
        self.collect_visible_skeins()
        self.populate_grid()

    def search(self, event):
        search_text = event.GetString()
        if not search_text:
            self.search_bar.SetValue('')
        # Update the search text in the model
        self.model.search(search_text)
        self.collect_visible_skeins()
        self.populate_grid()

    def add_skein(self, event):
        dialog = AddSkeinDialog(self, self.model)
        if dialog.ShowModal() == wx.ID_OK:
            if dialog.save_skein():
                wx.MessageBox("Skein added successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.collect_visible_skeins()
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
                self.populate_grid()
                self.collect_visible_skeins()

        dialog.Destroy()

    def update_skein_count(self, brand, sku, count):
        print(f"Updated skein count for {brand} - {sku} to {count}")
        self.SetStatusText(f"Updated skein count for {brand} - {sku} to {count}")
        # Update the count in the model
        self.model.update_skein_count(brand, sku, count)
        # Update the skein counter to reflect the new count
        self.collect_visible_skeins()

    def on_resize(self, event):
        # Allow the event to propagate
        event.Skip()

        # Recalculate the layout
        self.grid_sizer.Layout()
        self.scroll.FitInside()

    def on_close(self, event):
        self.defaults.update({
                "window_size": (self.GetSize().x, self.GetSize().y),
                "window_position": (self.GetPosition().x, self.GetPosition().y),
                "sort_method": self.model.sort_method
        })
        event.Skip()
