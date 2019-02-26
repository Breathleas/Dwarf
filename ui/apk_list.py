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
import os

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLineEdit

from lib.adb import Adb
from ui.list_view import DwarfListView


class ApkListDialog(QDialog):
    """ Dialog that shows installed apks and allows install
    """

    def __init__(self, parent=None, show_paths=False, show_install=False):
        super(ApkListDialog, self).__init__(parent=parent)
        self.setWindowTitle('Packages')

        v_box = QVBoxLayout()
        if show_install:
            h_box = QHBoxLayout()
            self.file_path = QLineEdit()
            self.file_path.setPlaceholderText('Path to apkfile for install')
            h_box.addWidget(self.file_path)
            self.install_button = QPushButton('Install')
            self.install_button.clicked.connect(self._on_install)
            h_box.addWidget(self.install_button)
            v_box.addLayout(h_box)

        self.apklist = ApkList(self, show_paths)
        self.apklist.retrieve_thread.onFinished.connect(self._on_finished)
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self._on_refresh)
        v_box.addWidget(self.apklist)
        v_box.addWidget(self.refresh_button)
        self.setLayout(v_box)

    # ************************************************************************
    # **************************** Functions *********************************
    # ************************************************************************

    # ************************************************************************
    # **************************** Handlers **********************************
    # ************************************************************************

    def _on_install(self):
        if self.file_path.text() is '':
            file_path = QFileDialog.getOpenFileName(self, 'Select an apk to install', QDir.currentPath(), '*.apk')

        if os.path.exists(self.file_path.text()):
            self.apklist.adb.install(file_path)

    def _on_refresh(self):
        self.refresh_button.setEnabled(False)
        self.apklist.refresh()

    def _on_finished(self):
        self.refresh_button.setEnabled(True)


class PackageRetrieveThread(QThread):
    """ Thread to retrieve installed packes via adb
    """
    onAddPackage = pyqtSignal(list, name='onAddPackage')
    onFinished = pyqtSignal(name='onFinished')
    onError = pyqtSignal(str, name='onError')

    def __init__(self, adb, parent=None):
        super(PackageRetrieveThread, self).__init__(parent=parent)
        self.adb = adb

        if not self.adb.is_available():
            return

    def run(self):
        """run
        """
        if self.adb.is_available():
            packages = self.adb.list_packages()
            for package in sorted(packages, key=lambda x: x.package):
                self.onAddPackage.emit([package.package, package.path])

        self.onFinished.emit()


class ApkList(DwarfListView):
    """ Displays installed APKs
    """

    def __init__(self, parent=None, show_path=True):
        super(ApkList, self).__init__(parent=parent)

        self.adb = Adb()

        if not self.adb.is_available():
            return

        self.retrieve_thread = PackageRetrieveThread(self.adb)
        if self.retrieve_thread is not None:
            self.retrieve_thread.onAddPackage.connect(self._on_addpackage)

        if show_path:
            self.apk_model = QStandardItemModel(0, 2)
        else:
            self.apk_model = QStandardItemModel(0, 1)

        self.apk_model.setHeaderData(0, Qt.Horizontal, 'Name')

        if show_path:
            self.apk_model.setHeaderData(1, Qt.Horizontal, 'Path')

        self.setModel(self.apk_model)

        if self.retrieve_thread is not None:
            if not self.retrieve_thread.isRunning():
                self.retrieve_thread.start()

    # ************************************************************************
    # **************************** Functions *********************************
    # ************************************************************************
    def refresh(self):
        """ Refresh Packages
        """
        if self.retrieve_thread is not None:
            if not self.retrieve_thread.isRunning():
                self.clear()
                self.retrieve_thread.start()

    # ************************************************************************
    # **************************** Handlers **********************************
    # ************************************************************************
    def _on_addpackage(self, package):
        if package:
            name = QStandardItem()
            name.setText(package[0])

            if self.apk_model.columnCount() == 2:
                path = QStandardItem()
                path.setText(package[1])

                self.apk_model.appendRow([name, path])
            else:
                self.apk_model.appendRow([name])
