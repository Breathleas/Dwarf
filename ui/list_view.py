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
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QTreeView

from lib.prefs import Prefs


class DwarfListView(QTreeView):
    """ Using QTreeView as ListView because it allows ListView+QHeaderView
    """

    def __init__(self, parent=None):
        super(DwarfListView, self).__init__(parent=parent)

        self._uppercase_hex = True

        _prefs = Prefs()
        self.rows_dualcolor = _prefs.get('dwarf_ui_alternaterowcolors', False)
        self.uppercase_hex = _prefs.get('dwarf_ui_hexstyle', 'upper').lower() == 'upper'

        self.setEditTriggers(self.NoEditTriggers)
        self.setHeaderHidden(False)
        self.setAutoFillBackground(True)
        self.setRootIsDecorated(False)
        # self.setSortingEnabled(True)

    # ************************************************************************
    # **************************** Properties ********************************
    # ************************************************************************
    @property
    def rows_dualcolor(self):
        """ AlternatingRowColors
        """
        return self.alternatingRowColors()

    @rows_dualcolor.setter
    def rows_dualcolor(self, value):
        """ AlternatingRowColors
        """
        if isinstance(value, bool):
            self.setAlternatingRowColors(value)
        elif isinstance(value, str):
            self.setAlternatingRowColors(value.lower() == 'true')

    @property
    def uppercase_hex(self):
        """ Addresses displayed lower/upper-case
        """
        return self._uppercase_hex

    @uppercase_hex.setter
    def uppercase_hex(self, value):
        """ Addresses displayed lower/upper-case
            value - bool or str
                    'upper', 'lower'
        """
        if isinstance(value, bool):
            self._uppercase_hex = value
        elif isinstance(value, str):
            self._uppercase_hex = (value == 'upper')

    # ************************************************************************
    # **************************** Functions *********************************
    # ************************************************************************
    def clear(self):
        """ Delete Entries but not Headerdata
        """
        # delete entries but not headerdata
        model = self.model()
        if model is not None:
            model.removeRows(0, model.rowCount())

    def get_item(self, index):
        """ Returns [] with col_texts
        """
        if self.model() is not None:
            item_data = []
            if index < self.model().rowCount():
                for i in range(self.model().columnCount()):
                    item_text = self.model().item(index, i).text()
                    if item_text:
                        item_data.append(item_text)
                    else:
                        item_data.append('')

                return item_data
            else:
                return None

    def get_item_text(self, index, col):
        """ returns text in index, col
        """
        if self.model() is not None:
            if index < self.model().rowCount():
                if col < self.model().columnCount():
                    item = self.model().item(index, col)
                    if isinstance(item, QStandardItem):
                        return self.model().item(index, col).text()

        return None

    def contains_text(self, text, case_sensitive=False):
        """ looks in all fields for text
            returns true if text exists
        """
        if self.model() is not None:
            for i in range(self.model().rowCount()):
                for j in range(self.model().columnCount()):
                    item_text = self.get_item_text(i, j)
                    if case_sensitive and (item_text == text):
                        return True
                    elif not case_sensitive and (item_text.lower() == text.lower()):
                        return True

        return False

    def number_of_items(self):
        """ returns number of rows
        """
        if self.model() is not None:
            return self.model().rowCount()
        else:
            return None

    def number_of_rows(self):
        """ returns number of rows
        """
        if self.model() is not None:
            return self.number_of_items()
        else:
            return None

    def number_of_total(self):
        """ returns number of all fields rows+cols
        """
        if self.model() is not None:
            return self.model().rowCount() + self.model().columnCount()
        else:
            return None

    def number_of_cols(self):
        """ returns number of cols
        """
        if self.model() is not None:
            return self.model().columnCount()
        else:
            return None

    # override doubleclickevent to prevent doublerightclicks
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mouseDoubleClickEvent(event)
