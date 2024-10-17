# -*- coding: utf-8 -*-
# amt/file_utils/pdfpreview.py

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

"""generate pdf preview"""

import fitz
from PySide6.QtGui import QImage, QPixmap

from amt.db.datamodel import EntryData

class PdfPreviewer:
    def __init__(self):
        self._cache: dict[EntryData, QPixmap] = {}

    def getPreview(self, entry: EntryData) -> QPixmap:
        try:
            qPixmap = self._cache[entry]
            return qPixmap
        except KeyError:
            qPixmap = self._generatePreview(entry)
            self._cache[entry] = qPixmap
            return qPixmap
        
    def _generatePreview(self, entry: EntryData) -> QPixmap:
        fileName = entry.fileName
        pdfDoc = fitz.open(fileName)
        page = pdfDoc.load_page(0)
        pixmap = page.get_pixmap()
        imageFormat = QImage.Format_RGBA8888 if pixmap.alpha else QImage.Format_RGB888
        image = QImage(pixmap.samples, pixmap.width, pixmap.height, pixmap.stride, imageFormat)
        qPixmap = QPixmap.fromImage(image)
        pdfDoc.close()
        return qPixmap
        