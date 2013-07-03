#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2013 elleryq@gmail.com
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

"""PDBContents"""
import logging

from pdbwidget import PDBWidget
from pageddatasource import PagedDataSource
from utils import convert_columns_to_pages
from PySide.QtCore import Qt
from PySide.QtCore import QPoint
from PySide.QtCore import Signal
from PySide.QtGui import QPainter
from PySide.QtGui import QPen
from PySide.QtGui import QRegion
from pdb import PDBFile


class PDBContents(PDBWidget):
    chapter_selected = Signal((int,))

    def __init__(self, parent=None):
        super(PDBContents, self).__init__(parent)
        self.old_rect = None
        self.recalc = True

    def get_cell_size(self):
        point_size = self.font().pointSize()
        cell_width = point_size * 2
        cell_height = point_size + point_size/3
        return (cell_width, cell_height)

    def do_calc(self):
        rect = self.rect()
        cell_width, cell_height = self.get_cell_size()
        self.x_pos_list = range(
            rect.width()-cell_width*2, rect.left()+cell_width, -cell_width)
        self.y_pos_list = range(10, rect.height()-10, (rect.height()-21))
        self.regions = [
            QRegion(x, self.y_pos_list[0], cell_width,
                    self.y_pos_list[-1]-self.y_pos_list[0])
            for x in self.x_pos_list[1:]]
        columns_in_page = len(self.x_pos_list) - 1
        self.datasource = PagedDataSource(convert_columns_to_pages(
            self.pdb.contents, columns_in_page))

        self.old_rect = rect

    def paintEvent(self, event):
        if not self.pdb:
            return False

        painter = QPainter(self)
        painter.setFont(self.font())

        # get canvas size
        rect = self.rect()

        cell_width, cell_height = self.get_cell_size()

        # draw grid
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.black))
        for x in self.x_pos_list:
            self._draw_line(painter, (
                x, self.y_pos_list[0]), (x, self.y_pos_list[-1]))
        for y in self.y_pos_list:
            self._draw_line(painter, (
                self.x_pos_list[0], y), (self.x_pos_list[-1], y))

        # draw page indicator
        if self.datasource.count_pages() > 1:
            seg = rect.width() / self.datasource.count_pages()
            x = rect.width() - (self.datasource.current_page+1)*seg
            self._draw_indicator(painter, x, rect.height()-1, seg)
        painter.restore()

        # Show contents
        # TODO: Show book name.
        painter.save()
        painter.setFont(self.font())
        start_x = 1
        start_y = 0
        columns_in_page = len(self.x_pos_list)
        try:
            for chapter_title in self.datasource.get_current_page():
                x = self.x_pos_list[start_x] + cell_width/4
                y = self.y_pos_list[start_y] + cell_height
                for c in chapter_title:
                    painter.drawText(x, y, c)
                    y = y + cell_height
                    if y > self.y_pos_list[-1]:
                        break
                start_x = start_x + 1
                if start_x > columns_in_page:
                    start_x = 1
        except IndexError, e:
            logging.error(e)
            logging.debug(
                "start_x=%d len(x_pos_list)=%d columns_in_page=%d " +
                "len(datasource.get_current_page())" % (
                    start_x, len(self.x_pos_list),
                    columns_in_page,
                    len(self.datasource.get_current_page())))
        painter.restore()

        return False

    def resizeEvent(self, event):
        super(PDBContents, self).resizeEvent(event)
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

    def mousePressEvent(self, event):
        if not self.pdb:
            return False
        self.chapter_selected.emit(self.which_chapter(event.x(), event.y()))
        return False

    def mouseMoveEvent(self, event):
        if not self.pdb:
            return False
        # TODO:
        logging.debug("which chapter? %d" % self.which_chapter(
            event.x(), event.y()))
        return False

    def keyPressEvent(self, event):
        flag = False
        if not self.pdb:
            return flag
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

    def which_chapter(self, x, y):
        selected = 0
        for r in self.regions:
            if r.contains(QPoint(int(x), int(y))):
                break
            selected = selected+1
        if self.datasource.current_page > 0:
            for page in self.datasource.pages[:self.datasource.current_page]:
                selected = selected + len(page)
        chapter = selected
        if chapter >= self.pdb.chapters:
            chapter = -1
        return chapter

if __name__ == "__main__":
    import sys
    import os
    from PySide.QtGui import QApplication
    from PySide.QtGui import QMainWindow

    def clicked(chapter):
        print(chapter)

    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            self.widget = PDBContents(self)
            self.pdbfile = PDBFile(os.path.realpath(sys.argv[-1])).parse()
            self.widget.set_pdb(self.pdbfile)
            self.widget.chapter_selected.connect(clicked)
            self.setCentralWidget(self.widget)
            self.resize(800, 600)

    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    app.exec_()
