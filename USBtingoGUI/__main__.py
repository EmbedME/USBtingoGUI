# This file is part of the USBtingoGUI project.
#
# Copyright(c) 2024 Thomas Fischl (https://www.fischl.de)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import queue
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, \
    QTableView, QPushButton, QCheckBox, QLabel, QComboBox, QSplitter, QDialog, QDialogButtonBox, \
    QHeaderView, QTextEdit, QLineEdit, QFileDialog
from PySide6.QtGui import QFontMetrics, QIcon
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, QSize, QSettings
import can
import time
from usbtingobus import USBtingoBus
from . import resources

class USBtingoGUI(QWidget):

    VERSION = "1.0"
    PROTOCOLS = {USBtingoBus.PROTOCOL_CAN_20: "CAN 2.0", USBtingoBus.PROTOCOL_CAN_FD: "CAN FD", USBtingoBus.PROTOCOL_CAN_FD_NONISO: "CAN FD NONISO"}
    BAUDRATES = [10000, 20000, 33333, 50000, 83333, 100000, 125000, 250000, 500000, 666666, 800000, 833333, 1000000, 2000000, 4000000, 5000000, 6666666, 8000000]
    MODES = {can.BusState.ACTIVE: "Active", can.BusState.PASSIVE: "Passive (listen-only)"}
    DLCS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64]
    SAMPLERATES = {1000000: "1 Msps", 5000000: "5 Msps", 10000000: "10 Msps", 20000000: "20 Msps", 30000000: "30 Msps", 40000000: "40 Msps"}
    OPERATINGMODES = ["Off", "Active", "Listenonly"]

    def __init__(self):
        self.canbus = None
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('USBtingoGUI v{}'.format(self.VERSION))
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowIcon(QIcon(":/icons/application.png"))
        self.settings = QSettings("EmbedME", "USBtingoGUI")

        # Create a horizontal splitter
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)

        # Create left side layout
        left_layout = QVBoxLayout()

        # Create a QTabWidget for left side
        left_tabs = QTabWidget()

        # Create Trace Tab
        self.trace_tableview = QTableView()
        self.message_model = TraceMessageTableModel()
        self.trace_tableview.setModel(self.message_model)
        self.trace_tableview.verticalHeader().setVisible(False)
        header = self.trace_tableview.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        font_metrics = QFontMetrics(self.trace_tableview.font())
        char_width = font_metrics.boundingRect('X').width()
        self.trace_tableview_singlerowheight = font_metrics.boundingRect("Xp").height()
        self.trace_tableview.verticalHeader().setDefaultSectionSize(self.trace_tableview_singlerowheight)
        self.trace_tableview.setColumnWidth(0, char_width * 16)
        self.trace_tableview.setColumnWidth(1, 15)
        self.trace_tableview.setColumnWidth(2, char_width * 10)
        self.trace_tableview.setColumnWidth(3, char_width * 4)
        self.trace_tableview.setShowGrid(False)
        self.trace_tableview.setAlternatingRowColors(True)
        left_tabs.addTab(self.trace_tableview, "Trace")

        # Create Monitor Tab
        self.monitor_tableview = QTableView()
        self.monitor_model = MonitorMessageTableModel()
        self.monitor_tableview.setModel(self.monitor_model)
        self.monitor_tableview.verticalHeader().setVisible(False)
        header = self.monitor_tableview.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        font_metrics = QFontMetrics(self.monitor_tableview.font())
        char_width = font_metrics.boundingRect('X').width()
        self.monitor_tableview_singlerowheight = font_metrics.boundingRect("Xp").height()
        self.monitor_tableview.verticalHeader().setDefaultSectionSize(self.monitor_tableview_singlerowheight)
        self.monitor_tableview.setColumnWidth(0, char_width * 8)
        self.monitor_tableview.setColumnWidth(1, char_width * 8)
        self.monitor_tableview.setColumnWidth(2, 15)
        self.monitor_tableview.setColumnWidth(3, char_width * 10)
        self.monitor_tableview.setColumnWidth(4, char_width * 4)
        self.monitor_tableview.setShowGrid(False)
        self.monitor_tableview.setAlternatingRowColors(True)
        left_tabs.addTab(self.monitor_tableview, "Monitor")

        # Create horizontal layout for buttons and label
        buttons_layout = QHBoxLayout()

        # Buttons and Label
        clear_button = QPushButton('Clear')
        save_button = QPushButton('Save')
        self.follow_button = QCheckBox('Follow')
        self.follow_button.setChecked(True)

        buttons_layout.addWidget(clear_button)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(self.follow_button)
        buttons_layout.addStretch() 

        clear_button.clicked.connect(self.clear)
        save_button.clicked.connect(self.save)

        left_layout.addWidget(left_tabs)
        left_layout.addLayout(buttons_layout)

        # Set left layout for the left side of the splitter
        left_side = QWidget()
        left_side.setLayout(left_layout)
        splitter.addWidget(left_side)

        # Create Settings layout
        settings_layout = QVBoxLayout()

        devicelist = can.detect_available_configs(interfaces=["usbtingo"])
        serialnumbers = [device['channel'] for device in devicelist]
        serialnumber_layout = QHBoxLayout()
        serialnumber_label = QLabel("Serialnumber:")
        self.serialnumber_combo = QComboBox()
        self.serialnumber_combo.addItems(serialnumbers)
        serialnumber_layout.addWidget(serialnumber_label)
        serialnumber_layout.addWidget(self.serialnumber_combo)
        settings_layout.addLayout(serialnumber_layout)

        protocol_layout = QHBoxLayout()
        protocol_label = QLabel("Protocol:")
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(self.PROTOCOLS.values())
        protocol_layout.addWidget(protocol_label)
        protocol_layout.addWidget(self.protocol_combo)
        settings_layout.addLayout(protocol_layout)        

        # Baudrate Nominal
        baudrate_nominal_layout = QHBoxLayout()
        baudrate_nominal_layout.addWidget(QLabel("Baudrate Nominal:"))
        self.baudrate_nominal_combo = QComboBox()
        self.baudrate_nominal_combo.setEditable(True)
        self.baudrate_nominal_combo.addItems([str(baudrate) for baudrate in self.BAUDRATES[:13]])
        baudrate_nominal_layout.addWidget(self.baudrate_nominal_combo)
        settings_layout.addLayout(baudrate_nominal_layout)

        # Baudrate Data
        baudrate_data_layout = QHBoxLayout()
        self.baudrate_data_label = QLabel("Baudrate Data:")
        baudrate_data_layout.addWidget(self.baudrate_data_label)
        self.baudrate_data_combo = QComboBox()
        self.baudrate_data_combo.setEditable(True)
        self.baudrate_data_combo.addItems([str(baudrate) for baudrate in self.BAUDRATES[-13:]])
        baudrate_data_layout.addWidget(self.baudrate_data_combo)
        settings_layout.addLayout(baudrate_data_layout)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(self.MODES.values())
        mode_layout.addWidget(self.mode_combo)
        settings_layout.addLayout(mode_layout)

        self.connect_button = QPushButton('Connect')
        self.connect_button.clicked.connect(self.handle_connect_button_click)
        settings_layout.addWidget(self.connect_button)

        settings_layout.addStretch()


        send_layout = QVBoxLayout()
        
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Id (hex):"))
        self.send_id_input = QLineEdit()
        self.send_id_input.setText("001")
        font_metrics = self.send_id_input.fontMetrics()
        text_width = font_metrics.horizontalAdvance(15 * 'X')
        self.send_id_input.setFixedWidth(text_width)
        self.send_id_input.textChanged.connect(self.send_id_changed)
        self.send_id_input.editingFinished.connect(self.format_id)
        self.send_id_input_style = self.send_id_input.styleSheet()
        id_layout.addWidget(self.send_id_input)
        send_layout.addLayout(id_layout)

        length_layout = QHBoxLayout()
        length_label = QLabel("Length:")
        length_layout.addWidget(length_label)
        self.send_length_combobox = QComboBox()
        self.send_length_combobox.addItems([str(dlc) for dlc in self.DLCS])
        self.send_length_combobox.setFixedWidth(text_width)
        length_layout.addWidget(self.send_length_combobox)
        send_layout.addLayout(length_layout)
        self.send_length_combobox.currentIndexChanged.connect(self.send_length_changed)

        flags_layout = QHBoxLayout()
        flags_layout.addWidget(QLabel("Flags:"))
        self.send_extended_button = QCheckBox('Ext')
        self.send_extended_button.stateChanged.connect(self.format_id)
        flags_layout.addWidget(self.send_extended_button)
        self.send_rtr_button = QCheckBox('RTR')        
        flags_layout.addWidget(self.send_rtr_button)
        self.send_fd_button = QCheckBox('FD')        
        flags_layout.addWidget(self.send_fd_button)
        self.send_brs_button = QCheckBox('Brs')
        flags_layout.addWidget(self.send_brs_button)
        send_layout.addLayout(flags_layout)

        send_layout.addWidget(QLabel("Data (hex):"))
        self.send_dataedit = QTextEdit()
        self.send_dataedit.textChanged.connect(self.send_data_changed)
        self.send_dataedit.setFixedHeight(self.send_dataedit.fontMetrics().height() * 9 + self.send_dataedit.frameWidth() * 2)
        self.send_dataedit_style = self.send_dataedit.styleSheet()
        send_layout.addWidget(self.send_dataedit)
        
        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(self.send)
        self.send_button.setEnabled(False)
        send_layout.addWidget(self.send_button)

        send_layout.addStretch()


        logic_layout = QVBoxLayout()
        description_label = QLabel(
            "Sample logic level on CAN-RX and save it in \nPulseView (sigrok project) compatible file for further analysis."
        )
        logic_layout.addWidget(description_label)
        logic_layout.addSpacing(20)

        samplerate_layout = QHBoxLayout()        
        samplerate_label = QLabel("Samplerate:")
        self.logic_samplerate_combobox = QComboBox()
        self.logic_samplerate_combobox.addItems(self.SAMPLERATES.values())
        self.logic_samplerate_combobox.setCurrentIndex(2)
        samplerate_layout.addWidget(samplerate_label)
        samplerate_layout.addWidget(self.logic_samplerate_combobox)
        logic_layout.addLayout(samplerate_layout)        
        logic_layout.addSpacing(20)

        filename_layout = QHBoxLayout()
        filename_label = QLabel("Filename:")
        self.logic_filename_edit = QLineEdit()
        self.logic_filename_edit.setText("usbtingo_capture.sr")
        logic_layout.addWidget(filename_label)
        filename_layout.addWidget(self.logic_filename_edit)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        filename_layout.addWidget(browse_button)
        logic_layout.addLayout(filename_layout)
        logic_layout.addSpacing(20)

        logic_buttons_layout = QHBoxLayout()
        self.logic_start_button = QPushButton("Start recording")
        self.logic_stop_button = QPushButton("Stop recording")
        self.logic_start_button.setEnabled(False)
        self.logic_stop_button.setEnabled(False)
        self.logic_start_button.clicked.connect(self.recording_start)
        self.logic_stop_button.clicked.connect(self.recording_stop)
        logic_buttons_layout.addWidget(self.logic_start_button)
        logic_buttons_layout.addWidget(self.logic_stop_button)
        logic_layout.addLayout(logic_buttons_layout)
        logic_layout.addStretch()

        status_layout = QVBoxLayout()
        statusflags = {
            "mode": "Operating mode:",
            "rxovf": "Overflow RX frames:",
            "txeovf" : "Overflow TX events:",
            "rec" : "Receive error counter (REC):",
            "tec" : "Transmit error counter (TEC):",
            "rp" : "Receive error passive:",
            "ep" : "Error passive:",
            "bo" : "Bus off:",
            "load" : "Bus load:",
        }
        self.status_labels = {}
        for key, label in statusflags.items():
            l = QHBoxLayout()
            l.addWidget(QLabel(label))
            self.status_labels[key] = QLabel()
            l.addWidget(self.status_labels[key])
            status_layout.addLayout(l)
        status_layout.addStretch()
        

        # Create right side tab widget
        self.right_tabs = QTabWidget()
        settings_widget = QWidget()
        settings_widget.setLayout(settings_layout)
        self.right_tabs.addTab(settings_widget, "Settings")
        send_widget = QWidget()
        send_widget.setLayout(send_layout)
        self.right_tabs.addTab(send_widget, "Send")
        logic_widget = QWidget()
        logic_widget.setLayout(logic_layout)
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        self.right_tabs.addTab(logic_widget, "Logic")
        self.right_tabs.addTab(status_widget, "Status")

        self.record_icon = QIcon(":/icons/record.png")
        self.record_tab_index = self.right_tabs.indexOf(logic_widget)
        self.status_icon = QIcon(":/icons/error.png")
        self.status_tab_index = self.right_tabs.indexOf(status_widget)

        # Set right tabs for the right side of the splitter
        splitter.addWidget(self.right_tabs)

        # Create main layout and add the splitter
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        splitter.setSizes([650, 350])

        self.setLayout(main_layout)

        self.protocol_combo.currentTextChanged.connect(self.handle_protocol_change)
        self.handle_protocol_change(self.protocol_combo.currentText())
        self.savesettings = {"serialnumber" : self.serialnumber_combo, "protocol" : self.protocol_combo, "baudrate_nominal" : self.baudrate_nominal_combo, "baudrate_data": self.baudrate_data_combo, "mode" : self.mode_combo}
        self.settings_load()

        self.message_model.rowsInserted.connect(self.autoScroll)

        if len(serialnumbers) == 0:
            self.show_message("error", "No USBtingo interface found!")

        self.statusreport_timeout = 0
        self.statusreport_queue = queue.Queue()
        self.updatereport_timer = QTimer(self)
        self.updatereport_timer.timeout.connect(self.statusreport_update)
        self.updatereport_timer.start(100)

    def settings_save(self):
        for name, combo in self.savesettings.items():
            self.settings.setValue(name, combo.currentText())
            
    def settings_load(self):
        for name, combo in self.savesettings.items():
            value = self.settings.value(name, type=str)
            if not value:
                continue
            
            if combo.isEditable():
                combo.setCurrentText(value)
            else:
                index = combo.findText(value)
                if index >= 0:
                    combo.setCurrentIndex(index)
        

    def closeEvent(self, event):
        if self.canbus is not None:
            self.canbus.shutdown()
        self.settings_save()
        
    def browse_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*)")
        if filename:
            self.logic_filename_edit.setText(filename)

    def autoScroll(self):
        if self.follow_button.isChecked():
            self.trace_tableview.scrollToBottom()

    def format_id(self):
        if self.send_id_input.hasFocus():
            return
        try:
            can_id = int(self.send_id_input.text(), 16)
            if self.send_extended_button.isChecked():
                hexstr = "{:08X}".format(can_id)
            else:
                hexstr = "{:03X}".format(can_id)
            self.send_id_input.setText(hexstr)
        except:
            pass


    def send_id_changed(self):
        try:
            can_id = int(self.send_id_input.text(), 16)
            if can_id > 0x7ff:
                self.send_extended_button.setChecked(True)
                self.send_extended_button.setEnabled(False)
            else:
                self.send_extended_button.setEnabled(True)

            self.send_id_input.setStyleSheet(self.send_id_input_style)
        except:
            self.send_id_input.setStyleSheet("border: 3px solid red;")
            self.send_extended_button.setEnabled(True)
        
    def update_flags(self):
        if self.protocol_combo.currentText() != self.PROTOCOLS[USBtingoBus.PROTOCOL_CAN_20]:
            self.trace_tableview.verticalHeader().setDefaultSectionSize(self.trace_tableview_singlerowheight * 2)
            self.monitor_tableview.verticalHeader().setDefaultSectionSize(self.monitor_tableview_singlerowheight * 2)
            self.send_brs_button.setEnabled(True)
            self.send_rtr_button.setChecked(False)
            self.send_rtr_button.setEnabled(False)
            while self.send_length_combobox.count() < len(self.DLCS):
                self.send_length_combobox.addItem(str(self.DLCS[self.send_length_combobox.count()]))
            length = int(self.send_length_combobox.currentText())
            if length > 8:
                self.send_fd_button.setChecked(True)
                self.send_fd_button.setEnabled(False)
            else:
                self.send_fd_button.setEnabled(True)
                
        else:
            self.trace_tableview.verticalHeader().setDefaultSectionSize(self.trace_tableview_singlerowheight)
            self.monitor_tableview.verticalHeader().setDefaultSectionSize(self.monitor_tableview_singlerowheight)
            self.send_rtr_button.setEnabled(True)
            self.send_fd_button.setChecked(False)
            self.send_brs_button.setChecked(False)
            self.send_fd_button.setEnabled(False)
            self.send_brs_button.setEnabled(False)
            last_index = self.send_length_combobox.count() - 1
            for index in range(last_index, 8, -1):
                self.send_length_combobox.removeItem(index)
            
    def get_send_data(self):
        data_hex = self.send_dataedit.toPlainText().split()        
        return bytearray.fromhex(''.join(data_hex))

    def send_length_changed(self):        
        length = int(self.send_length_combobox.currentText())
        try:
            data = self.get_send_data()
            if len(data) != length and not self.send_dataedit.hasFocus():
                data = data[:length]
                data.extend(bytes(length - len(data)))
                hex_string = ' '.join(format(byte, '02X') for byte in data)
                self.send_dataedit.setText(hex_string)                
        except:
            pass
        self.update_flags()

    def send_data_changed(self):
        try:
            data = self.get_send_data()
            self.send_dataedit.setStyleSheet(self.send_dataedit_style)

            length = 64
            for dlc in self.DLCS:
                if dlc >= len(data):
                    length = dlc
                    break            
            self.send_length_combobox.setCurrentText(str(length))        
        except:
            self.send_dataedit.setStyleSheet("border: 3px solid red;")


    def show_message(self, msgtype, message):
        self.message_model.add_message(MessageNotification(msgtype, message))

    def send(self):
        can_id = int(self.send_id_input.text(), 16)
        data = self.get_send_data()
        message = can.Message(
            arbitration_id=can_id,
            is_extended_id=self.send_extended_button.isChecked(),
            is_fd=self.send_fd_button.isChecked(),
            is_remote_frame=self.send_rtr_button.isChecked(),
            bitrate_switch=self.send_brs_button.isChecked(),
            dlc=int(self.send_length_combobox.currentText()),
            data=data)
        
        self.canbus.send(message, timeout=0) 

    def handle_protocol_change(self, text):
        enable = text != self.PROTOCOLS[USBtingoBus.PROTOCOL_CAN_20]
        self.baudrate_data_label.setEnabled(enable)
        self.baudrate_data_combo.setEnabled(enable)
        self.update_flags()

    def handle_connect_button_click(self):
        if self.connect_button.text() == "Disconnect":
            self.disconnect()
        else:
            self.connect()                

    def connect(self):
        protocol = list(self.PROTOCOLS.keys())[self.protocol_combo.currentIndex()]
        baudrate_nominal = int(self.baudrate_nominal_combo.currentText())
        baudrate_data = int(self.baudrate_data_combo.currentText())
        mode = list(self.MODES.keys())[self.mode_combo.currentIndex()]
        self.canbus = USBtingoBus(serial=self.serialnumber_combo.currentText(), protocol=protocol, bitrate=baudrate_nominal, data_bitrate=baudrate_data, state=mode, receive_own_messages=True)
        
        self.mode_combo.setEnabled(False)
        self.protocol_combo.setEnabled(False)
        self.serialnumber_combo.setEnabled(False)
        self.baudrate_nominal_combo.setEnabled(False)
        self.baudrate_data_combo.setEnabled(False)
        self.send_button.setEnabled(True)
        self.logic_start_button.setEnabled(True)
        self.logic_stop_button.setEnabled(False)

        self.show_message("info", "Connected to USBtingo (FW{}{}/HW{})".format(str(self.canbus.firmware_version_major).zfill(2), str(self.canbus.firmware_version_minor).zfill(2), self.canbus.hardware_model_id))
        self.connect_button.setText("Disconnect")

        can.Notifier(self.canbus, [self.received_message])
        self.canbus.statusreport_listener_add(self.statusreport_listener)

    def disconnect(self):
        self.show_message("info", "Disconnected")
        
        self.canbus.shutdown()
        self.canbus = None

        self.mode_combo.setEnabled(True)
        self.protocol_combo.setEnabled(True)
        self.serialnumber_combo.setEnabled(True)
        self.baudrate_nominal_combo.setEnabled(True)
        self.send_button.setEnabled(False)
        self.logic_start_button.setEnabled(False)
        self.logic_stop_button.setEnabled(False)
        self.protocol_combo.currentTextChanged.connect(self.handle_protocol_change)
        self.connect_button.setText("Connect")

    def recording_start(self):
        samplingrate = list(self.SAMPLERATES.keys())[self.logic_samplerate_combobox.currentIndex()]
        filename = self.logic_filename_edit.text()
        self.canbus.recording_start(filename=filename, samplingrate=samplingrate)
        self.logic_start_button.setEnabled(False)
        self.logic_stop_button.setEnabled(True)
        self.show_message("info", "Started logic recording")
        self.right_tabs.setTabIcon(self.record_tab_index, self.record_icon)


    def recording_stop(self):
        self.canbus.recording_stop()
        self.logic_start_button.setEnabled(True)
        self.logic_stop_button.setEnabled(False)
        self.show_message("info", "Stopped logic recording")
        self.right_tabs.setTabIcon(self.record_tab_index, QIcon())
        

    def statusreport_listener(self, report):
        self.statusreport_queue.put_nowait(report)        

    def statusreport_update(self):

        if self.statusreport_timeout <= 20:
            self.statusreport_timeout = self.statusreport_timeout + 1
            
        while self.canbus and not self.statusreport_queue.empty():
            self.statusreport_timeout = 0
            error = False
            report = self.statusreport_queue.get(False)

            load = (47 * report.stats_std + 65 * report.stats_ext + 8 * report.stats_data) / self.canbus.bitrate + (8 * report.stats_dataBRS) / self.canbus.data_bitrate
            if load > 100:
                load = 100
            self.status_labels["load"].setText("{:.0%}".format(load))
            
            self.status_labels["mode"].setText(self.OPERATINGMODES[report.mode])
            self.status_labels["tec"].setText(str(report.getTEC()))
            self.status_labels["rec"].setText(str(report.getREC()))
            statusflags = {
                "rxovf" : report.overflow & 1,
                "txeovf" : report.overflow & 2,
                "rp": report.isReceiveErrorPassive(),
                "ep": report.isErrorPassive(),
                "bo": report.isBusOff(),
                }
            for key, value in statusflags.items():
                if value:
                    error = True
                    self.status_labels[key].setText("ERROR")
                    self.status_labels[key].setStyleSheet("color: red")
                else:
                    self.status_labels[key].setText("OK")
                    self.status_labels[key].setStyleSheet("color: green")

            if error:
                self.right_tabs.setTabIcon(self.status_tab_index, self.status_icon)
            else:
                self.right_tabs.setTabIcon(self.status_tab_index, QIcon())

        if self.statusreport_timeout == 20:
            self.statusreport_clear()

    def statusreport_clear(self):
        for key in self.status_labels.keys():
            self.status_labels[key].setText("")
        self.right_tabs.setTabIcon(self.status_tab_index, QIcon())

    def received_message(self, message):
        self.message_model.add_message(message)
        self.monitor_model.add_message(message)
        
    def clear(self):
        self.message_model.clear()
        self.monitor_model.clear()

    def save(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*)")
        if filename:
            with open(filename, 'w') as logfile:
                for message in self.message_model.messages:
                    if isinstance(message, MessageNotification):
                        logfile.write("{:>14.5f} CXX {} {}\n".format(message.timestamp, message.msgtype, message.message))
                    else:
                        if message.is_rx:
                            typecode = "R"
                        else:
                            typecode = "T"
                        if message.is_extended_id:
                            idcode = "29"
                        else:
                            idcode = "11"
                        hexdata = ' '.join('{:02X}'.format(byte) for byte in message.data)
                        logfile.write("{:>14.5f} {}{} {:X} {}\n".format(message.timestamp, typecode, idcode, message.arbitration_id, hexdata))
                logfile.close()
                self.show_message("info", "Saved messages to file")

        
class MessageNotification(object):
    def __init__(self, msgtype, message):
        self.msgtype = msgtype
        self.message = message
        self.timestamp = time.time()

class MonitorMessage(object):
    def __init__(self, canmessage):
        self.lastcanmessage = canmessage
        self.period = 0
        self.count = 1

class TraceMessageTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self.icons = [QIcon(":/icons/receive.png"), QIcon(":/icons/send.png"), QIcon(":/icons/error.png"), QIcon(":/icons/info.png")]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "Timestamp"
            elif section == 1:
                return ""
            elif section == 2:
                return "Id"
            elif section == 3:
                return "DLC"
            elif section == 4:
                return "Data"
        return super().headerData(section, orientation, role)

    def rowCount(self, parent=QModelIndex()):
        return len(self.messages)

    def columnCount(self, parent=QModelIndex()):
        return 5

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid() or \
                not (0 <= index.row() < len(self.messages)) or \
                not (0 <= index.column() < 5):
            return None

        message = self.messages[index.row()]

        if isinstance(message, MessageNotification):
            
            if role == Qt.DisplayRole:
                if index.column() == 0:
                    return '{:>14.5f}'.format(message.timestamp)
                if index.column() == 4:
                    return message.message
                
            elif role == Qt.DecorationRole and index.column() == 1:
                if message.msgtype == "info":
                    return self.icons[3]
                else:
                    return self.icons[2]

        else:

            if role == Qt.DisplayRole:
                if index.column() == 0:
                    return '{:>14.5f}'.format(message.timestamp)
                elif index.column() == 2:
                    if message.is_extended_id:
                        return '{:08X}'.format(message.arbitration_id)
                    else:
                        return '{:03X}'.format(message.arbitration_id)
                elif index.column() == 3:
                    return message.dlc
                elif index.column() == 4:
                    if message.is_remote_frame:
                        return "Remote Transmission Request"
                    else:
                        hexstring = ' '.join('{:02X}'.format(byte) for byte in message.data)
                        hexstring = '\n'.join(hexstring[i:i+96] for i in range(0, len(hexstring), 96))
                        return hexstring
                
            elif role == Qt.DecorationRole and index.column() == 1:
                if message.is_rx:
                    return self.icons[0]
                else:
                    return self.icons[1]

            elif role == Qt.TextAlignmentRole:
                if index.column() == 2:
                    return Qt.AlignRight | Qt.AlignVCenter
                elif index.column() == 3:
                    return Qt.AlignCenter

        return None

    def add_message(self, message):
        self.beginInsertRows(QModelIndex(), len(self.messages), len(self.messages))
        self.messages.append(message)
        self.endInsertRows()
        
    def clear(self):
        self.messages = []
        self.layoutChanged.emit()

class MonitorMessageTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self.messages_dict = {}
        self.icons = [QIcon(":/icons/receive.png"), QIcon(":/icons/send.png"), QIcon(":/icons/error.png"), QIcon(":/icons/info.png")]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "Period"
            elif section == 1:
                return "Count"
            elif section == 2:
                return ""
            elif section == 3:
                return "Id"
            elif section == 4:
                return "DLC"
            elif section == 5:
                return "Data"
        return super().headerData(section, orientation, role)

    def rowCount(self, parent=QModelIndex()):
        return len(self.messages)

    def columnCount(self, parent=QModelIndex()):
        return 6

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid() or \
                not (0 <= index.row() < len(self.messages)) or \
                not (0 <= index.column() < 6):
            return None

        m = self.messages[index.row()]
        message = m.lastcanmessage

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return '{:>6.1f}'.format(m.period * 1000)
            elif index.column() == 1:
                return m.count
            elif index.column() == 3:
                if message.is_extended_id:
                    return '{:08X}'.format(message.arbitration_id)
                else:
                    return '{:03X}'.format(message.arbitration_id)
            elif index.column() == 4:
                return message.dlc
            elif index.column() == 5:
                if message.is_remote_frame:
                    return "Remote Transmission Request"
                else:
                    hexstring = ' '.join('{:02X}'.format(byte) for byte in message.data)
                    hexstring = '\n'.join(hexstring[i:i+96] for i in range(0, len(hexstring), 96))
                    return hexstring
            
        elif role == Qt.DecorationRole and index.column() == 2:
            if message.is_rx:
                return self.icons[0]
            else:
                return self.icons[1]

        elif role == Qt.TextAlignmentRole:
            if index.column() == 0 or index.column() == 3:
                return Qt.AlignRight | Qt.AlignVCenter
            elif index.column() == 1 or index.column == 4:
                return Qt.AlignCenter

        return None

    def add_message(self, message):
        
        key = message.arbitration_id << 2
        if message.is_extended_id:
            key = key | 1
        if not message.is_rx:
            key = key | 2

        if key in self.messages_dict:
            m = self.messages_dict.get(key)
            m.period = message.timestamp - m.lastcanmessage.timestamp
            m.count = m.count + 1
            m.lastcanmessage = message
            self.dataChanged.emit(self.index(m.tableindex, 0), self.index(m.tableindex, 5)) 
        else:
            m = MonitorMessage(message)
            m.tableindex = len(self.messages)
            self.messages_dict[key] = m
            self.beginInsertRows(QModelIndex(), len(self.messages), len(self.messages))
            self.messages.append(m)
            self.endInsertRows()
        
    def clear(self):
        self.messages = []
        self.messages_dict = {}
        self.layoutChanged.emit()

def main():
    app = QApplication(sys.argv)

    ex = USBtingoGUI()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

