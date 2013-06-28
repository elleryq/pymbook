#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2010 elleryq@gmail.com
#
#  This file is part of pymbook
#  pymbook is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  pymbook is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with pymbook.  If not, see <http://www.gnu.org/licenses/>.

"""PDBCanvas"""
import logging

from pdbwidget import PDBWidget
from pageddatasource import PagedDataSource
from utils import convert_pdb_to_pages
from PySide.QtCore import Qt
from PySide.QtGui import QPainter
from PySide.QtGui import QPen
from pdb import PDBFile


class PDBCanvas(PDBWidget):
    #__gsignals__ = dict(tell_callback=(gobject.SIGNAL_RUN_FIRST,
    #                                  gobject.TYPE_NONE,
    #                                  (gobject.TYPE_INT, gobject.TYPE_INT)))

    def __init__(self, parent=None):
        super(PDBCanvas, self).__init__(parent)
        self.old_rect = None
        self.datasource = None
        self.chapter = 0
        self.page = 0
        self.setFocusPolicy(Qt.StrongFocus)

    def set_pdb(self, pdb):
        super(PDBCanvas, self).set_pdb(pdb)
        self.chapter = 0
        self.page = 0

    def set_chapter(self, chapter):
        if not self.pdb:
            return

        self.chapter = chapter

        if not self.datasource:
            self.do_calc()

        page = self._search_chapter(chapter)
        if not page:
            page = 0
        logging.debug("chapter %d is in page %d" % (self.chapter, page))
        self.set_page(page)

    def set_page(self, page):
        self.page = page
        if self.datasource:
            self.datasource.current_page = page
            self.redraw_canvas()

    def do_calc(self):
        # get canvas size
        rect = self.rect()
        point_size = self.font().pointSize()
        cell_width = point_size + point_size
        cell_height = point_size + point_size / 2

        self.x_pos_list = range(
            rect.width()-cell_width*2, rect.top()+cell_width, -cell_width)
        self.y_pos_list = range(
            cell_height, rect.height()-cell_height, cell_height)
        columns_in_page = len(self.x_pos_list)
        glyphs_in_column = len(self.y_pos_list)
        self.source = convert_pdb_to_pages(
            self.pdb, columns_in_page, glyphs_in_column)
        self.datasource = PagedDataSource(self.source)
        found_page = self._search_chapter(self.chapter)
        if not found_page:
            found_page = 0
        logging.debug("found_page=%d", found_page)
        self.datasource.current_page = found_page
        if self.page:
            logging.debug("self.page=%d", self.page)
            self.datasource.current_page = self.page
        self.old_rect = rect
        self.chapter_seg = rect.width()/self.pdb.chapters

    #def configure(self, widget, event):
    #    if not self.pdb:
    #        return False
    #
    #    self.do_calc()

    def paintEvent(self, event):
        if not self.pdb:
            return False

        painter = QPainter(self)
        painter.setFont(self.font())

        rect = self.rect()

        # TODO: Is here a better place?
        self._tell()

        logging.debug("pdbcanvas.expose: current_page={0}".format(
            self.datasource.current_page))

        # draw chapter indicator
        if self.pdb.chapters > 1:
            x = rect.width() - (
                self.datasource.get_current_page()[0]+1) * self.chapter_seg
            self._draw_indicator(painter, x, 0, self.chapter_seg)

        # draw page in chapter indicator
        if self.datasource.count_pages() > 1:
            seg = rect.width() / self._count_chapter_pages(
                self.datasource.get_current_page()[0])
            x = rect.width()-(self.datasource.get_current_page()[1]+1)*seg
            self._draw_indicator(painter, x, rect.height()-1, seg)

        # draw text
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(self.font())
        page = self.datasource.get_current_page()[2]
        col = 0
        for x in self.x_pos_list:
            if col >= len(page):
                break
            column = page[col]
            pos = 0
            for y in self.y_pos_list:
                if pos >= len(column):
                    break
                painter.drawText(x, y, column[pos])
                pos = pos+1
            col = col+1

        painter.restore()

    def _tell(self):
        #self.emit("tell_callback", self.chapter, self.datasource.current_page)
        pass

    def _count_chapter_pages(self, chapter):
        if not self.source:
            return -1
        pages = [ch for ch, n_in_p, p in self.source if ch == chapter]
        return len(pages)

    def _search_chapter(self, chapter):
        """
        According the specified page number to search chapter.
        Return the chapter number if found, else return None.
        """
        found = None
        page_count = 0
        for chap, n_in_page, page in self.source:
            if chap == chapter:
                found = page_count
                break
            page_count = page_count + 1
        return found

    def keyPressEvent(self, event):
        flag = False
        if not self.pdb:
            return super(PDBCanvas, self).keyPressEvent(event)
        flag = True
        prev_list = [Qt.Key_PageUp, Qt.Key_Up, Qt.Key_K]
        next_list = [Qt.Key_PageDown, Qt.Key_Down, Qt.Key_J]
        if event.key() in prev_list:
            self.datasource.go_previous()
        elif event.key() in next_list:
            self.datasource.go_next()
        else:
            flag = False
        self.redraw_later()
        return flag

    def resizeEvent(self, event):
        super(PDBCanvas, self).resizeEvent(event)
        self.do_calc()

    def wheelEvent(self, event):
        if not self.pdb:
            return False

        if event.delta() > 0:
            self.datasource.go_previous()
        else:
            self.datasource.go_next()
        self.redraw_later()
        event.accept()

if __name__ == "__main__":
    import sys
    import os
    from PySide.QtGui import QApplication
    from PySide.QtGui import QMainWindow

    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            self.widget = PDBCanvas(self)
            self.pdbfile = PDBFile(os.path.realpath(sys.argv[-1])).parse()
            self.widget.set_pdb(self.pdbfile)
            self.setCentralWidget(self.widget)

    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    app.exec_()
