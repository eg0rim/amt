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
from PySide6.QtWidgets import QApplication

from amt.db.datamodel import EntryData
from amt.logger import getLogger

logger = getLogger(__name__)

class PdfPreviewer:
    def __init__(self, size: tuple[int, int] = (210,297)):
        self._cache: dict[EntryData, QPixmap | None] = {}
        #self._dpr = QApplication.primaryScreen().devicePixelRatio()
        self._dpr = 1.
        self._size = (int(size[0] * self._dpr), int(size[1] * self._dpr))
        
    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, size: tuple[int, int]):
        self._size = (int(size[0] * self._dpr), int(size[1] * self._dpr))
        self.clearCache()

    def getPreview(self, entry: EntryData) -> QPixmap | None:
        try:
            qPixmap = self._cache[entry]
            return qPixmap
        except KeyError:
            qPixmap = self._generatePreview(entry)
            self._cache[entry] = qPixmap
            return qPixmap
        
    def _generatePreview(self, entry: EntryData) -> QPixmap | None:
        try:
            fileName = entry.fileName
            pdfDoc = fitz.open(fileName)
            page = pdfDoc.load_page(0)
            origSize = (page.rect.width, page.rect.height)
            zoomX = self._size[0] / origSize[0]
            zoomY = self._size[1] / origSize[1]
            zoom = min(zoomX, zoomY)
            zoomMatrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=zoomMatrix)
            imageFormat = QImage.Format_RGBA8888 if pixmap.alpha else QImage.Format_RGB888
            image = QImage(pixmap.samples, pixmap.width, pixmap.height, pixmap.stride, imageFormat)
            qPixmap = QPixmap.fromImage(image)
            pdfDoc.close()
            return qPixmap
        except Exception as e:
            logger.error(f"Failed to generate preview for {entry.fileName}: {e}")
            return None
        
    def clearCache(self):
        self._cache.clear()