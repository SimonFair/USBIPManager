# Software configuration
from library import config
# Modal window interfaces
from library.modal.CapturingSettings import CapturingSettingUI

#
from re import findall
#
from json import loads, load, dump
#
from os import listdir, path, remove
# PyQt5 modules
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem, QWidget, QHBoxLayout, QCheckBox, QGroupBox, QDialog, QLineEdit, \
    QRadioButton, QHeaderView, QTableWidgetItem, QComboBox, QFileDialog


#
def text_changed(obj):
    obj.setStyleSheet("")


class CapturingTreeFilling(object):
    def __init__(self, _self, srv_addr):
        #
        self._self = _self
        self.srv_addr = srv_addr
        self.capturing = config.get_capturing_config()
        if self.capturing.has_section(srv_addr):
            for row in self.capturing[self.srv_addr]:
                dev_bus = row.split("[")[0]
                child_id = findall(r"\[(.*?)\]", row).pop()
                child_data = loads(self.capturing[self.srv_addr].get(row))
                self.add_device(dev_bus)
                self.add_child(dev_bus, child_id, child_data)

    def add_device(self, dev_bus):
        if not self.get_device(dev_bus):
            self._self.capturing_tree.addTopLevelItem(QTreeWidgetItem([dev_bus]))
            self._self.capturing_tree.expandAll()

    def add_child(self, dev_bus, child_id, child_data):
        dev_bus = self.get_device(dev_bus)
        custom_name, byte_index, matching = child_data
        child = QTreeWidgetItem(["Port ID: " + child_id, custom_name, ", ".join(byte_index), ", ".join(matching)])
        dev_bus.addChild(child)

    def get_device(self, dev_bus):
        # Getting the device tree root and counting children
        root = self._self.capturing_tree.invisibleRootItem()
        child_count = root.childCount()
        # Looping through children range and getting certain server address
        for child in range(child_count):
            device = root.child(child)
            if device.text(0) == dev_bus:
                return device


class HubPortSelection(QWidget):
    def __init__(self, data, parent=None):
        # noinspection PyArgumentList
        super(HubPortSelection, self).__init__(parent)

        layout = QHBoxLayout()
        for idx, port in enumerate(data, 1):
            checkbox = QCheckBox()
            checkbox.setText("{0}".format(idx))
            if port:
                checkbox.setChecked(True)
            # noinspection PyArgumentList
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)


class ServerSettingUI(QDialog):
    def __init__(self, parent=None, srv_addr=None):
        # noinspection PyArgumentList
        super(ServerSettingUI, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        uic.loadUi("ui/modal/ServerSettings.ui", self)
        self.srv_addr = srv_addr

        # Window title
        self.setWindowTitle(self.windowTitle() + " {0}".format(self.srv_addr))

        # Getting configuration and setting parameters of modal window input fields
        self.config = config.get_config()
        for param in config.default_srv_ini:
            obj = getattr(self, param)
            if isinstance(obj, QLineEdit):
                obj.setText(self.config[self.srv_addr][param])
                # noinspection PyUnresolvedReferences
                obj.textChanged.connect(lambda text, linedit=obj: text_changed(linedit))
            if isinstance(obj, QRadioButton):
                obj.setChecked(self.config[self.srv_addr].getboolean(param))
                obj.clicked.connect(self.checking_auth_type)
            if isinstance(obj, QCheckBox) or isinstance(obj, QGroupBox):
                obj.setChecked(self.config[self.srv_addr].getboolean(param))

        # Setting a mask on the password fields
        self.auth_password.setEchoMode(QLineEdit.Password)
        self.key_passphrase.setEchoMode(QLineEdit.Password)

        # Reading the hub configuration directory and filling the combobox
        for file in listdir("hub"):
            if file.endswith(".json"):
                filename, _ = path.splitext(file)
                self.hub_json.addItem(filename)

        #
        self.hub_json.currentIndexChanged.connect(self.checking_hub_json)
        # Setting a non-existent index to force a dropdown menu check
        self.hub_json.setCurrentIndex(-1)
        self.hub_json.setCurrentIndex(
            self.hub_json.findText(self.config[self.srv_addr]["hub_json"], Qt.MatchFixedString))

        # Save hub configuration button action
        self.hub_conf_save.clicked.connect(self.save_hub_json)
        # Insert hub configuration row button action
        self.hub_conf_insert.clicked.connect(self.insert_row_hub_json)
        # Delete hub configuration row button action
        self.hub_conf_delete.clicked.connect(self.delete_row_hub_json)

        #
        self.apply_button.clicked.connect(self.apply_action)
        self.cancel_button.clicked.connect(self.close)
        self.select_button.clicked.connect(self.file_dialog)

        #
        self.capturing_insert.clicked.connect(self.insert_capturing)

        #
        self.checking_auth_type()

        #
        CapturingTreeFilling(self, self.srv_addr)

    #
    def checking_auth_type(self):
        if self.auth_type_key.isChecked():
            self.auth_ssh_port.setEnabled(True)
            self.auth_username.setEnabled(True)
            self.auth_password.setEnabled(False)
            self.key_path.setEnabled(True)
            self.key_passphrase.setEnabled(True)
            self.select_button.setEnabled(True)
        elif self.auth_type_password.isChecked():
            self.auth_ssh_port.setEnabled(True)
            self.auth_username.setEnabled(True)
            self.auth_password.setEnabled(True)
            self.key_path.setEnabled(False)
            self.key_passphrase.setEnabled(False)
            self.select_button.setEnabled(False)
        elif self.auth_type_none.isChecked():
            self.auth_ssh_port.setEnabled(False)
            self.auth_username.setEnabled(False)
            self.auth_password.setEnabled(False)
            self.key_path.setEnabled(False)
            self.key_passphrase.setEnabled(False)
            self.select_button.setEnabled(False)

    #
    def checking_hub_json(self):
        # Reading current selected configuration
        try:
            with open(path.join("hub", "{0}.json".format(self.hub_json.currentText()))) as fp:
                conf = load(fp)
        # Disabling hub configuration objects in the absence of the configuration file
        except FileNotFoundError:
            self.hub_conf.setRowCount(0)
            self.hub_conf.setEnabled(False)
            self.hub_timeout.setEnabled(False)
            self.hub_conf_save.setEnabled(False)
            self.hub_conf_insert.setEnabled(False)
            self.hub_conf_delete.setEnabled(False)
            return

        # Enabling hub configuration objects in the presence of the configuration file
        self.hub_conf.setEnabled(True)
        self.hub_timeout.setEnabled(True)
        self.hub_conf_save.setEnabled(True)
        self.hub_conf_insert.setEnabled(True)
        self.hub_conf_delete.setEnabled(True)
        #
        self.hub_conf.setRowCount(len(conf))
        header = self.hub_conf.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for idx, hub_id in enumerate(conf):
            item = QTableWidgetItem(hub_id)
            item.setTextAlignment(Qt.AlignCenter)
            self.hub_conf.setItem(idx, 0, item)
            self.hub_conf.setCellWidget(idx, 1, HubPortSelection(conf[hub_id]))

    #
    def save_hub_json(self):
        # Default empty configuration array
        conf = dict()

        # Reading configuration parameters and filling array
        for row in range(self.hub_conf.rowCount()):
            #
            hub_id = self.hub_conf.item(row, 0).text()
            conf[hub_id] = list()
            #
            layout = self.hub_conf.cellWidget(row, 1).layout()
            ports = (layout.itemAt(i).widget() for i in range(layout.count()))
            for port in ports:
                conf[hub_id].append(port.isChecked() * 1)

        # Saving configuration to the json file
        # TODO File selection dialog
        with open(path.join("hub", "{0}.json".format(self.hub_json.currentText())), "w") as fp:
            dump(conf, fp)

        # Setting up the alert message
        config.alert_box("Success", "Configuration successfully saved!", 1)

    #
    def insert_row_hub_json(self):
        row_position = self.hub_conf.rowCount()
        self.hub_conf.insertRow(row_position)
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        self.hub_conf.setItem(row_position, 0, item)
        self.hub_conf.setCellWidget(row_position, 1, HubPortSelection([0] * 7))

    #
    def delete_row_hub_json(self):
        config.table_row_delete(self.hub_conf)

    #
    def insert_capturing(self):
        device_capturing = CapturingSettingUI(self, self.srv_addr)
        device_capturing.show()

    # Saving server parameters to the configuration file
    def apply_action(self):
        # TODO Checking for the presence of empty required input fields when activating parameters such as USB, SSH, etc
        # Checking for empty string in obligatory line edit list
        if config.is_empty([self.search_filter]):
            return

        # Updating configuration
        remove("config.ini")
        for param in config.default_srv_ini:
            obj = getattr(self, param)
            if isinstance(obj, QLineEdit):
                self.config.set(self.srv_addr, param, str(obj.text()))
            if isinstance(obj, QComboBox):
                self.config.set(self.srv_addr, param, str(obj.currentText()))
            if isinstance(obj, QRadioButton) or isinstance(obj, QCheckBox) or isinstance(obj, QGroupBox):
                self.config.set(self.srv_addr, param, str(obj.isChecked()))

        # Saving configuration to the ini file
        with open("config.ini", "a", encoding="utf-8") as f:
            self.config.write(f)

        # Closing the modal window
        self.close()

    def file_dialog(self):
        options = QFileDialog.Options()
        # noinspection PyCallByClass
        filename, _ = QFileDialog.getOpenFileName(self, "Selecting key", "", "All Files (*)", options=options)
        if filename:
            self.key_path.setText(filename)
