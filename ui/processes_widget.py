"""
Dwarf - Copyright (C) 2019 Giovanni Rocca (iGio90)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
"""
import frida

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget, QHeaderView, QVBoxLayout, QPushButton

from ui.list_view import DwarfListView


class ProcsThread(QThread):
    """ Updates Processlist
        signals:
            clear_proc()
            add_proc(NotEditableListWidgetItem)
            is_error(str) - shows str in statusbar
        device must set before run
    """
    add_proc = pyqtSignal(dict)
    is_error = pyqtSignal(str)
    is_finished = pyqtSignal()

    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        if isinstance(device, frida.core.Device):
            self.device = device

    def run(self):
        """ run
        """
        if self.device is not None:
            if isinstance(self.device, frida.core.Device):
                try:
                    procs = self.device.enumerate_processes()

                    for proc in procs:
                        proc_item = {'pid': proc.pid, 'name': proc.name}
                        self.add_proc.emit(proc_item)
                # ServerNotRunningError('unable to connect to remote frida-server: closed')
                except frida.ServerNotRunningError:
                    self.is_error.emit('unable to connect to remote frida server: not started')
                except frida.TransportError:
                    self.is_error.emit('unable to connect to remote frida server: closed')
                except frida.TimedOutError:
                    self.is_error.emit('unable to connect to remote frida server: timedout')
                except Exception:
                    self.is_error.emit('something was wrong...')

        self.is_finished.emit()


class ProcessList(QWidget):
    """ ProcessListWidget wich shows running Processes on Device

        args:
            device needed

        Signals:
            onProcessSelected([pid, name]) - pid(int) name(str)
            onRefreshError(str)
    """

    onProcessSelected = pyqtSignal(list, name='onProcessSelected')
    onRefreshError = pyqtSignal(str, name='onRefreshError')

    def __init__(self, device, parent=None):
        super(ProcessList, self).__init__(parent=parent)

        if not isinstance(device, frida.core.Device):
            return

        self._device = device

        self.process_list = DwarfListView()

        model = QStandardItemModel(0, 2, parent)
        model.setHeaderData(0, Qt.Horizontal, "PID")
        model.setHeaderData(0, Qt.Horizontal, Qt.AlignCenter, Qt.TextAlignmentRole)
        model.setHeaderData(1, Qt.Horizontal, "Name")

        self.process_list.doubleClicked.connect(self._on_item_clicked)

        v_box = QVBoxLayout()
        v_box.setContentsMargins(0, 0, 0, 0)
        v_box.addWidget(self.process_list)
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self._on_refresh_procs)
        self.refresh_button.setEnabled(False)
        v_box.addWidget(self.refresh_button)
        self.setLayout(v_box)

        self.process_list.setModel(model)
        self.process_list.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        self.procs_update_thread = ProcsThread(self, self._device)
        self.procs_update_thread.add_proc.connect(self._on_add_proc)
        self.procs_update_thread.is_error.connect(self._on_error)
        self.procs_update_thread.is_finished.connect(self._on_refresh_finished)
        self.procs_update_thread.device = self._device
        self.procs_update_thread.start()

    # ************************************************************************
    # **************************** Properties ********************************
    # ************************************************************************
    @property
    def device(self):
        """ Sets Device needs frida.core.device
        """
        return self._device

    @device.setter
    def device(self, value):
        self.set_device(value)

    # ************************************************************************
    # **************************** Functions *********************************
    # ************************************************************************
    def clear(self):
        """ Clears the List
        """
        self.process_list.clear()

    def set_device(self, device):
        """ Set frida Device
        """
        if isinstance(device, frida.core.Device):
            self._device = device
            self.procs_update_thread.device = device

    # ************************************************************************
    # **************************** Handlers **********************************
    # ************************************************************************
    def _on_item_clicked(self, model_index):
        model = self.process_list.model()

        index = model.itemFromIndex(model_index).row()

        if index != -1:
            sel_pid = self.process_list.get_item_text(index, 0)
            sel_name = self.process_list.get_item_text(index, 1)
            self.onProcessSelected.emit([int(sel_pid), sel_name])

    def _on_add_proc(self, item):
        model = self.process_list.model()
        pid = QStandardItem()
        pid.setText(str(item['pid']))
        pid.setTextAlignment(Qt.AlignCenter)
        name = QStandardItem()
        name.setText(item['name'])

        model.appendRow([pid, name])

    def _on_error(self, error_str):
        self.onRefreshError.emit(error_str)

    def _on_refresh_procs(self):
        if not self._device:
            return

        if not self.procs_update_thread.isRunning():
            self.clear()
            self.refresh_button.setEnabled(False)
            self.procs_update_thread.device = self._device
            self.procs_update_thread.start()

    def _on_refresh_finished(self):
        self.refresh_button.setEnabled(True)
