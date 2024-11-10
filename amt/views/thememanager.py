# -*- coding: utf-8 -*-
# amt/views/thememanager.py

# Copyright (c) 2024 Egor Im
# This file is part of Article Management Tool.
# Article Management Tool is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as published 
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Article Management Tool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""class for managing themes"""

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPalette

class ThemeManager:
    """ 
    Class for managing themes.
    """
    themes = ["light", "dark"]
        
    @classmethod
    def setTheme(cls, themename: str):
        if themename in cls.themes:
            QIcon.setThemeName(themename)
        else:
            raise ValueError("Theme not found")
    
    @classmethod
    def deduceTheme(cls, widget: QWidget):
        if widget.palette().color(QPalette.Window).lightness() > 128:
            cls.setTheme("light")
        else:
            cls.setTheme("dark")
        