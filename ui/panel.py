import wx


class ColorDisplayPanel(wx.Panel):
    def __init__(self, parent, skein):
        super().__init__(parent, size=wx.Size(100, 100))
        self.skein = skein
        self.SetMinSize(wx.Size(100, 400))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.average_lightness = self.calculate_average_lightness(self.skein.color)
        self.render_buffer: wx.Bitmap | None = None

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        if not self.render_buffer:
            self.render()
        dc.DrawBitmap(self.render_buffer, 0, 0)
        event.Skip()

    def render(self):
        print(f'Rendering {self.skein.name}')
        width, height = self.GetSize()
        self.render_buffer = wx.Bitmap(width, height)

        dc = wx.MemoryDC(self.render_buffer)

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
        print(f'Making Panel for {skein.name}')
        super().__init__(parent, size=wx.Size(150, 200))
        self.skein = skein
        self.count = count
        self.brand = skein.brand
        self.sku = skein.sku
        self.is_visible = True

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
        self.color_panel.render_buffer = None
        self.color_panel.Refresh()
        event.Skip()

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