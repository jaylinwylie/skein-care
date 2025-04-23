from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QAction
import json
import os

from skein import Skein, Catalog


class SkeinWidget(QtWidgets.QWidget):
    countChanged = Signal(int)

    def __init__(self, skein: Skein, count: int = 0, parent=None):
        super().__init__(parent)
        self.skein = skein
        self.count = count

        self.setMinimumSize(100, 100)
        self.setMaximumHeight(100)
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)

        # Calculate average color
        average_color = [0, 0, 0]
        for color in skein.color:
            average_color[0] += color[0]
            average_color[1] += color[1]
            average_color[2] += color[2]

        average_color[0] /= len(skein.color)
        average_color[1] /= len(skein.color)
        average_color[2] /= len(skein.color)

        # Calculate relative luminance
        luminance = (0.299 * average_color[0] +
                     0.587 * average_color[1] +
                     0.114 * average_color[2]) / 255

        # Use white text for dark backgrounds, black text for light backgrounds
        text_color = [0, 0, 0] if luminance > 0.5 else [255, 255, 255]
        text_color_str = f"rgb({text_color[0]}, {text_color[1]}, {text_color[2]})"
        text_color_str_a = f"rgba({text_color[0]}, {text_color[1]}, {text_color[2]}, 128)"

        # Create label for skein info
        self.infoLabel = QtWidgets.QLabel(f"{skein.brand.upper()}\n{skein.sku}\n{skein.name}")
        self.infoLabel.setAlignment(Qt.AlignCenter)
        self.infoLabel.setWordWrap(True)
        self.infoLabel.setStyleSheet(f"color: {text_color_str}")

        # Create custom spinbox layout
        spinbox_container = QtWidgets.QHBoxLayout()
        spinbox_container.setSpacing(0)
        spinbox_container.setContentsMargins(0, 0, 0, 0)

        button_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {text_color_str};
            }}
            QPushButton:hover {{
                background: {text_color_str_a};
            }}
        """

        # Create minus button
        self.minus_button = QtWidgets.QPushButton("-")
        self.minus_button.setFixedSize(25, 25)
        self.minus_button.clicked.connect(self._decrease_value)
        self.minus_button.setStyleSheet(button_style)

        # Create the number display
        self.value_label = QtWidgets.QLineEdit(str(count))
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedWidth(40)
        self.value_label.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {text_color_str};
            }}
        """)
        self.value_label.setReadOnly(True)

        # Create plus button
        self.plus_button = QtWidgets.QPushButton("+")
        self.plus_button.setFixedSize(25, 25)
        self.plus_button.clicked.connect(self._increase_value)
        self.plus_button.setStyleSheet(button_style)

        # Add widgets to the container
        spinbox_container.addWidget(self.minus_button)
        spinbox_container.addWidget(self.value_label)
        spinbox_container.addWidget(self.plus_button)

        # Add widgets to layout
        layout.addWidget(self.infoLabel)
        layout.addLayout(spinbox_container)

        # Set layout margins
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)



    def _decrease_value(self):
        current = int(self.value_label.text())
        if current > 0:
            new_value = current - 1
            self.value_label.setText(str(new_value))
            self.count = new_value
            self.countChanged.emit(new_value)

    def _increase_value(self):
        current = int(self.value_label.text())
        if current < 999:
            new_value = current + 1
            self.value_label.setText(str(new_value))
            self.count = new_value
            self.countChanged.emit(new_value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), Qt.GlobalColor.darkGray)

        # Draw border
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Draw color bands
        colors = self.skein.color
        if not colors:
            colors = [[200, 200, 200]]  # Default gray if no color

        num_colors = len(colors)
        if num_colors == 1:
            # Single color - fill the whole area
            r, g, b = colors[0]
            painter.fillRect(self.rect(), QColor(r, g, b))
        else:
            # Multiple colors - draw horizontal bands
            band_width = self.width() / num_colors
            for i, color in enumerate(colors):
                r, g, b = color
                band_rect = QtCore.QRect(
                        int(i * band_width),
                        0,
                        int(band_width),
                        self.height()
                )
                painter.fillRect(band_rect, QColor(r, g, b))


class ColorWidget(QtWidgets.QWidget):
    colorChanged = Signal(list)

    def __init__(self, color=None, parent=None):
        super().__init__(parent)
        self.color = color or [255, 255, 255]

        # Set up the widget
        self.setMinimumSize(50, 50)
        self.setMaximumSize(50, 50)

        # Enable mouse tracking for click events
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw border
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Fill with color
        r, g, b = self.color
        painter.fillRect(self.rect().adjusted(1, 1, -1, -1), QColor(r, g, b))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            color = QtWidgets.QColorDialog.getColor(QColor(self.color[0], self.color[1], self.color[2]), self)
            if color.isValid():
                self.color = [color.red(), color.green(), color.blue()]
                self.update()
                self.colorChanged.emit(self.color)


class AddSkeinDialog(QtWidgets.QDialog):
    def __init__(self, catalog, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.colors = [[255, 255, 255]]  # Default to white

        self.setWindowTitle("Add New Skein")
        self.setMinimumWidth(400)

        layout = QtWidgets.QVBoxLayout(self)

        # Brand input
        brand_layout = QtWidgets.QHBoxLayout()
        brand_label = QtWidgets.QLabel("Brand:\t")
        self.brand_input = QtWidgets.QLineEdit()
        brand_layout.addWidget(brand_label)
        brand_layout.addWidget(self.brand_input)
        layout.addLayout(brand_layout)

        # SKU input
        sku_layout = QtWidgets.QHBoxLayout()
        sku_label = QtWidgets.QLabel("SKU:\t")
        self.sku_input = QtWidgets.QLineEdit()
        sku_layout.addWidget(sku_label)
        sku_layout.addWidget(self.sku_input)
        layout.addLayout(sku_layout)

        # Name input
        name_layout = QtWidgets.QHBoxLayout()
        name_label = QtWidgets.QLabel("Name:\t")
        self.name_input = QtWidgets.QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Colors section
        colors_layout = QtWidgets.QVBoxLayout()
        colors_label = QtWidgets.QLabel("Colours:\t")
        colors_layout.addWidget(colors_label)

        # Color widgets container
        self.colors_container = QtWidgets.QWidget()
        self.colors_container_layout = QtWidgets.QHBoxLayout(self.colors_container)
        self.colors_container_layout.setAlignment(Qt.AlignLeft)

        # Add initial color widget
        self.add_color_widget(self.colors[0])

        # Add/Remove color buttons
        color_buttons_layout = QtWidgets.QHBoxLayout()
        add_color_button = QtWidgets.QPushButton("Add Color")
        add_color_button.clicked.connect(self.add_color)
        remove_color_button = QtWidgets.QPushButton("Remove Color")
        remove_color_button.clicked.connect(self.remove_color)
        color_buttons_layout.addWidget(add_color_button)
        color_buttons_layout.addWidget(remove_color_button)

        colors_layout.addWidget(self.colors_container)
        colors_layout.addLayout(color_buttons_layout)
        layout.addLayout(colors_layout)

        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_color_widget(self, color):
        color_widget = ColorWidget(color)
        color_widget.colorChanged.connect(self.update_color)
        self.colors_container_layout.addWidget(color_widget)

    def add_color(self):
        self.colors.append([255, 255, 255])
        self.add_color_widget(self.colors[-1])

    def remove_color(self):
        if len(self.colors) > 1:
            self.colors.pop()
            item = self.colors_container_layout.takeAt(self.colors_container_layout.count() - 1)
            if item.widget():
                item.widget().deleteLater()

    def update_color(self, color):
        sender = self.sender()
        index = 0
        for i in range(self.colors_container_layout.count()):
            if self.colors_container_layout.itemAt(i).widget() == sender:
                index = i
                break
        self.colors[index] = color

    def get_skein_data(self):
        return {
            "brand": self.brand_input.text(),
            "sku": self.sku_input.text(),
            "name": self.name_input.text(),
            "colors": self.colors
        }

    def save_skein(self):
        data = self.get_skein_data()
        brand = data["brand"]
        sku = data["sku"]

        if not brand or not sku:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Brand and SKU are required.")
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
                QtWidgets.QMessageBox.warning(self, "Error", f"Error loading brand file: {e}")
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
            QtWidgets.QMessageBox.warning(self, "Error", f"Error saving brand file: {e}")
            return False

        # Add to catalog
        if brand not in self.catalog.skeins:
            self.catalog.skeins[brand] = {}

        skein = Skein(brand, sku)
        skein.name = data["name"]
        skein.color = data["colors"]
        self.catalog.skeins[brand][sku] = skein

        return True


class Window(QtWidgets.QMainWindow):
    def __init__(self, library: dict, catalog: Catalog, parent=None):
        super().__init__(parent)
        self.library = library
        self.catalog = catalog
        self.show_all = True  # Default to showing all skeins
        self.search_text = ""  # Initialize empty search text

        # Set window properties
        self.setWindowTitle("Skein Care")
        self.setMinimumSize(400, 600)

        # Dont allow resizing
        self.setFixedSize(self.size())

        # Create central widget and main layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # Create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        # Add "Add New Skein" action
        add_skein_action = QAction("Add New Skein", self)
        add_skein_action.triggered.connect(self.show_add_skein_dialog)
        file_menu.addAction(add_skein_action)

        # Add separator
        file_menu.addSeparator()

        # Add toggle for showing/hiding skeins not in library
        self.toggle_action = QAction("Show All Skeins", self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(True)
        self.toggle_action.toggled.connect(self.toggle_skeins_visibility)
        file_menu.addAction(self.toggle_action)

        # Create search bar
        search_layout = QtWidgets.QHBoxLayout()
        search_label = QtWidgets.QLabel("Search:")
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search by SKU or name...")
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_bar)
        main_layout.addLayout(search_layout)

        # Create scroll area for skeins grid
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Create widget to hold the grid
        self.grid_widget = QtWidgets.QWidget()
        scroll_area.setWidget(self.grid_widget)

        # Create grid layout for skeins
        self.grid_layout = QtWidgets.QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignTop)

        # Populate the grid with skeins
        self.populate_grid()

    def populate_grid(self):
        # Clear existing widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Track position in grid
        row, col = 0, 0
        max_cols = 5  # Number of columns in the grid

        # Add skein widgets to the grid
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

                # Create skein widget
                skein_widget = SkeinWidget(skein, count)
                skein_widget.countChanged.connect(lambda value, b=brand, s=sku: self.update_skein_count(b, s, value))

                # Add to grid
                self.grid_layout.addWidget(skein_widget, row, col)

                # Move to next position
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def toggle_skeins_visibility(self, show_all):
        self.show_all = show_all
        if show_all:
            self.toggle_action.setText("Show All Skeins")
        else:
            self.toggle_action.setText("Show Library Only")
        self.populate_grid()

    def on_search_text_changed(self, text):
        self.search_text = text
        self.populate_grid()

    def show_add_skein_dialog(self):
        dialog = AddSkeinDialog(self.catalog, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            if dialog.save_skein():
                QtWidgets.QMessageBox.information(self, "Success", "Skein added successfully.")
                self.populate_grid()  # Refresh the grid to show the new skein

    def update_skein_count(self, brand, sku, count):
        # Ensure brand exists in library
        if brand not in self.library:
            self.library[brand] = {}

        # Update count
        self.library[brand][sku] = count
