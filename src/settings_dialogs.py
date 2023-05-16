from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, \
    QPushButton, QStyle
from data_store import HomographyPoint


class AddNewPointDialog(QDialog):
    def __init__(self, edit_mode=False):
        super().__init__()
        self.setWindowTitle("Add New Stage Point")

        self.buttonBox = QDialogButtonBox()
        self.create_btn = QPushButton("Create Point")
        self.cancel_btn = QPushButton("Cancel")
        self.create_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogOkButton")))
        self.cancel_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogCancelButton")))
        self.buttonBox.addButton(self.cancel_btn, QDialogButtonBox.RejectRole)
        self.buttonBox.addButton(self.create_btn, QDialogButtonBox.AcceptRole)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

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
        verticalLayout.addWidget(self.buttonBox)

        self.setLayout(verticalLayout)

    def unit_changed(self, unit_id):
        multipliers = [1, 10, 1000, 25.4, 304.8, 914.4]
        self.current_unit_multiplier = multipliers[unit_id]


class EditPointDialog(AddNewPointDialog):
    def __init__(self, name: str, hom: HomographyPoint):
        super().__init__()
        self.setWindowTitle("Edit Stage Point")
        self.delete_status = False

        self.pt_label_input.setText(name)
        self.x_input.setText(str(hom.world_coord.x()))
        self.y_input.setText(str(hom.world_coord.y()))
        self.z_input.setText(str(hom.world_coord.z()))

        self.create_btn.setText("Save Edits")
        self.delete_btn = QPushButton("Delete Point")
        self.delete_btn.clicked.connect(self.delete_callback)
        self.create_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogSaveButton")))
        self.delete_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogDiscardButton")))
        self.buttonBox.addButton(self.delete_btn, QDialogButtonBox.RejectRole)

    def delete_callback(self):
        self.delete_status = True
