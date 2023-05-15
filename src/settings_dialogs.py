from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox


class AddNewPointDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Stage Point")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        verticalLayout = QVBoxLayout()
        verticalLayout.setSpacing(12)

        # Label:
        horizontalNameLayout = QHBoxLayout()
        name_label = QLabel("Point Label:")
        self.pt_label_input = QLineEdit("Upstage Left")
        horizontalNameLayout.addWidget(name_label)
        horizontalNameLayout.addWidget(self.pt_label_input)

        # Coordinates:
        message = QLabel("Please enter the measurements to the new stage point from your chosen reference point")
        horizontalLayout = QHBoxLayout()
        x_label = QLabel("Width:")
        self.x_input = QLineEdit("0")
        y_label = QLabel("Depth:")
        self.y_input = QLineEdit("0")
        z_label = QLabel("Height:")
        self.z_input = QLineEdit("0")
        for widget in [x_label, self.x_input, y_label, self.y_input, z_label, self.z_input]:
            horizontalLayout.addWidget(widget)

        # Unit selection:
        self.current_unit_multiplier = 1
        self.unitSelect = QComboBox()
        self.unitSelect.addItems(["mm", "cm", "m", "in", "ft", "yd"])
        self.unitSelect.currentIndexChanged.connect(self.unit_changed)
        unitLabel = QLabel("Measurement Unit:")
        horizontalUnitLayout = QHBoxLayout()
        horizontalUnitLayout.addWidget(unitLabel)
        horizontalUnitLayout.addWidget(self.unitSelect)

        # Add all to dialog layout:
        verticalLayout.addLayout(horizontalNameLayout)
        verticalLayout.addWidget(message)
        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addLayout(horizontalUnitLayout)
        verticalLayout.addWidget(buttonBox)

        self.setLayout(verticalLayout)

    def unit_changed(self, unit_id):
        multipliers = [1, 10, 1000, 25.4, 304.8, 914.4]
        self.current_unit_multiplier = multipliers[unit_id]

