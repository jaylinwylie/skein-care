import wx
import wx.grid
import json
import os
from skein import Skein

wxEVT_COUNT_CHANGED = wx.NewEventType()
EVT_COUNT_CHANGED = wx.PyEventBinder(wxEVT_COUNT_CHANGED, 1)


class CountChangedEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, value=0):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self.value = value

    def get_value(self):
        return self.value


class SkeinPanel(wx.Panel):
    def __init__(self, parent, skein, count=0):
        super().__init__(parent, size=wx.Size(100, 100))
        self.skein = skein
        self.count = count
        self.SetMinSize(wx.Size(100, 100))
        self.SetMaxSize(wx.Size(-1, 100))

        average_color = [0, 0, 0]
        for color in skein.color:
            average_color[0] += color[0]
            average_color[1] += color[1]
            average_color[2] += color[2]

        average_color[0] /= len(skein.color)
        average_color[1] /= len(skein.color)
        average_color[2] /= len(skein.color)

        luminance = (0.299 * average_color[0] +
                     0.587 * average_color[1] +
                     0.114 * average_color[2]) / 255

        self.text_color = wx.BLACK if luminance > 0.5 else wx.WHITE

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.info_label = wx.StaticText(self, label=f"{skein.brand.upper()}\n{skein.sku}\n{skein.name}")
        self.info_label.SetForegroundColour(self.text_color)

        spinbox_sizer = wx.BoxSizer()

        self.minus_button = wx.Button(self, label="-", size=wx.Size(35, 35))
        self.minus_button.Bind(wx.EVT_BUTTON, self._decrease_value)

        self.value_text = wx.TextCtrl(self, value=str(count), size=wx.Size(70, 35), style=wx.TE_CENTER)

        self.plus_button = wx.Button(self, label="+", size=wx.Size(35, 35))
        self.plus_button.Bind(wx.EVT_BUTTON, self._increase_value)

        spinbox_sizer.Add(self.minus_button, 0, wx.ALIGN_CENTER)
        spinbox_sizer.Add(self.value_text, 0, wx.ALIGN_CENTER)
        spinbox_sizer.Add(self.plus_button, 0, wx.ALIGN_CENTER)

        sizer.Add(self.info_label, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(spinbox_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)

        self.SetSizer(sizer)

        self.Bind(wx.EVT_PAINT, self.on_paint)

    def _decrease_value(self, event):
        current = int(self.value_text.GetValue())
        if current > 0:
            new_value = current - 1
            self.value_text.SetValue(str(new_value))
            self.count = new_value
            evt = CountChangedEvent(wxEVT_COUNT_CHANGED, self.GetId(), new_value)
            wx.PostEvent(self, evt)

    def _increase_value(self, event):
        current = int(self.value_text.GetValue())
        if current < 999:
            new_value = current + 1
            self.value_text.SetValue(str(new_value))
            self.count = new_value
            evt = CountChangedEvent(wxEVT_COUNT_CHANGED, self.GetId(), new_value)
            wx.PostEvent(self, evt)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)

        # Get the size of the panel
        width, height = self.GetSize()

        # Draw background
        gc.SetBrush(wx.Brush(wx.Colour(64, 64, 64)))
        gc.DrawRectangle(0, 0, width, height)

        # Draw border
        gc.SetPen(wx.Pen(wx.BLACK, 1))
        gc.DrawRectangle(0, 0, width, height)

        # Draw color bands
        colors = self.skein.color
        if not colors:
            colors = [[200, 200, 200]]  # Default gray if no color

        num_colors = len(colors)
        if num_colors == 1:
            # Single color - fill the whole area
            r, g, b = colors[0]
            gc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
            gc.DrawRectangle(0, 0, width, height)
        else:
            # Multiple colors - draw horizontal bands
            band_width = width / num_colors
            for i, color in enumerate(colors):
                r, g, b = color
                gc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
                gc.DrawRectangle(i * band_width, 0, band_width, height)


class ColorPanel(wx.Panel):
    def __init__(self, parent, color=None):
        super().__init__(parent, size=wx.Size(50, 50))
        self.color = color or [255, 255, 255]
        self.SetMinSize(wx.Size(50, 50))
        self.SetMaxSize(wx.Size(50, 50))

        # Bind events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)

        # Get the size of the panel
        width, height = self.GetSize()

        # Draw border
        gc.SetPen(wx.Pen(wx.BLACK, 1))
        gc.DrawRectangle(0, 0, width, height)

        # Fill with color
        r, g, b = self.color
        gc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
        gc.DrawRectangle(1, 1, width-2, height-2)

    def on_click(self, event):
        color_data = wx.ColourData()
        color_data.SetColour(wx.Colour(self.color[0], self.color[1], self.color[2]))

        dlg = wx.ColourDialog(self, color_data)
        if dlg.ShowModal() == wx.ID_OK:
            wx_color = dlg.GetColourData().GetColour()
            self.color = [wx_color.Red(), wx_color.Green(), wx_color.Blue()]
            self.Refresh()

            # Notify parent of color change
            evt = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.GetId())
            evt.SetEventObject(self)
            wx.PostEvent(self.GetParent(), evt)

        dlg.Destroy()


class AddSkeinDialog(wx.Dialog):
    def __init__(self, parent, catalog):
        super().__init__(parent, title="Add New Skein")
        self.catalog = catalog
        self.colors = [[255, 255, 255]]  # Default to white

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
        self.add_color_panel(self.colors[0])

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

    def add_color_panel(self, color):
        color_panel = ColorPanel(self.colors_panel, color)
        color_panel.Bind(wx.EVT_BUTTON, self.update_color)
        self.colors_sizer.Add(color_panel, 0, wx.RIGHT, 5)
        self.colors_panel.Layout()

    def add_color(self, event):
        self.colors.append([255, 255, 255])
        self.add_color_panel(self.colors[-1])

    def remove_color(self, event):
        if len(self.colors) > 1:
            self.colors.pop()
            # Remove the last color panel
            self.colors_sizer.GetItem(self.colors_sizer.GetItemCount() - 1).GetWindow().Destroy()
            self.colors_panel.Layout()

    def update_color(self, event):
        # Find which color panel was changed
        panel = event.GetEventObject()
        index = 0
        for i in range(self.colors_sizer.GetItemCount()):
            if self.colors_sizer.GetItem(i).GetWindow() == panel:
                index = i
                break
        self.colors[index] = panel.color

    def get_skein_data(self):
        return {
            "brand": self.brand_input.GetValue(),
            "sku": self.sku_input.GetValue(),
            "name": self.name_input.GetValue(),
            "colors": self.colors
        }

    def save_skein(self):
        data = self.get_skein_data()
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
            "color": data["colors"]
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
        skein.color = data["colors"]
        self.catalog.skeins[brand][sku] = skein

        return True


class Window(wx.Frame):
    def __init__(self, library, catalog, parent=None):
        super().__init__(parent, title="Skein Care", size=wx.Size(800, 600))
        self.library = library
        self.catalog = catalog
        self.show_all = True  # Default to showing all skeins
        self.search_text = ""  # Initialize empty search text

        # Create the main panel and sizer
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create a menu bar
        menubar = wx.MenuBar()
        file_menu = wx.Menu()

        # Add "Add New Skein" menu item
        add_skein_item = file_menu.Append(wx.ID_ANY, "Add New Skein")
        self.Bind(wx.EVT_MENU, self.show_add_skein_dialog, add_skein_item)

        # Add separator
        file_menu.AppendSeparator()

        # Add toggle for showing/hiding skeins not in library
        self.toggle_item = file_menu.AppendCheckItem(wx.ID_ANY, "Show All Skeins")
        self.toggle_item.Check(True)
        self.Bind(wx.EVT_MENU, self.toggle_skeins_visibility, self.toggle_item)

        menubar.Append(file_menu, "&File")
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

        # Populate the grid with skeins
        self.populate_grid()

        # Set a minimum size
        self.SetMinSize(self.GetSize())

    def populate_grid(self):
        # Clear existing widgets
        self.grid_sizer.Clear(True)

        # Add skein panels to the grid
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

                # Create skein panel
                skein_panel = SkeinPanel(self.scroll, skein, count)
                skein_panel.Bind(EVT_COUNT_CHANGED, lambda evt, b=brand, s=sku: self.update_skein_count(b, s, evt.get_value()))

                # Add to grid
                self.grid_sizer.Add(skein_panel, 0, wx.EXPAND)

        # Update layout
        self.grid_sizer.Layout()
        self.scroll.FitInside()

    def toggle_skeins_visibility(self, event):
        self.show_all = event.IsChecked()
        if self.show_all:
            self.toggle_item.SetItemLabel("Show All Skeins")
        else:
            self.toggle_item.SetItemLabel("Show Library Only")
        self.populate_grid()

    def search(self, event):
        self.search_text = event.GetString()
        self.populate_grid()

    def show_add_skein_dialog(self, event):
        dialog = AddSkeinDialog(self, self.catalog)
        if dialog.ShowModal() == wx.ID_OK:
            if dialog.save_skein():
                wx.MessageBox("Skein added successfully.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.populate_grid()
        dialog.Destroy()

    def update_skein_count(self, brand, sku, count):
        if brand not in self.library:
            self.library[brand] = {}
        self.library[brand][sku] = count
