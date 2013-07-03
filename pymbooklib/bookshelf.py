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

"""Bookshelf widget"""
import logging

from utils import find_pdbs
from utils import convert_columns_to_pages
from pageddatasource import PagedDataSource
from PySide.QtCore import Qt
from PySide.QtCore import Signal
from PySide.QtCore import QPoint
from PySide.QtGui import QPainter
from PySide.QtGui import QRegion
from PySide.QtGui import QPen
from pdbwidget import PDBWidget


class BookshelfWidget(PDBWidget):
    book_selected = Signal((str,))

    def __init__(self, parent=None, shelf_path=""):
        super(BookshelfWidget, self).__init__(parent)
        self.books = find_pdbs(shelf_path)
        self.do_calc()

    def get_cell_size(self):
        return (self.font().pointSize()*2,
                self.font().pointSize()+self.font().pointSize()/3)

    def do_calc(self):
        rect = self.rect()
        cell_width, cell_height = self.get_cell_size()
        self.x_pos_list = range(rect.width()-cell_width*2,
                                rect.x()+cell_width, -cell_width)
        self.y_pos_list = range(0, rect.height(), (rect.height()-1))
        self.regions = [
            QRegion(x, self.y_pos_list[0], cell_width,
                    self.y_pos_list[-1]-self.y_pos_list[0])
            for x in self.x_pos_list[1:]]
        columns_in_page = len(self.x_pos_list)-1
        self.datasource = PagedDataSource(convert_columns_to_pages(
                                          self.books, columns_in_page))

    def draw_string(self, painter, s, x, y, limit):
        cell_width, cell_height = self.get_cell_size()
        for c in s:
            painter.drawText(x, y, c)
            y = y + cell_height
            if y > limit:
                break

    def paintEvent(self, event):
        if not self.books:
            return False

        painter = QPainter(self)

        # get canvas size
        rect = self.rect()

        cell_width, cell_height = self.get_cell_size()

        # draw grid
        painter.setPen(QPen(Qt.GlobalColor.black))
        for x in self.x_pos_list:
            self._draw_line(painter, (x, self.y_pos_list[0]),
                            (x, self.y_pos_list[-1]))
        for y in self.y_pos_list:
            self._draw_line(painter, (self.x_pos_list[0], y),
                            (self.x_pos_list[-1], y))

        # draw page indicator
        if self.datasource.count_pages() > 1:
            seg = rect.width() / self.datasource.count_pages()
            x = rect.width()-(self.datasource.current_page+1)*seg
            self._draw_indicator(painter, x, rect.height()-1, seg)

        # Show shelf
        painter.save()
        painter.setFont(self.font())
        start_x = 1
        start_y = 0
        columns_in_page = len(self.x_pos_list)
        try:
            padding_left = cell_width/4
            for book_name, pdb_filename in self.datasource.get_current_page():
                self.draw_string(painter, book_name,
                                 self.x_pos_list[start_x] + padding_left,
                                 self.y_pos_list[start_y] + cell_height,
                                 self.y_pos_list[-1])
                start_x = start_x + 1
                if start_x > columns_in_page:
                    start_x = 1
        except IndexError, e:
            logging.error(e)
            logging.debug("start_x=%d len(x_pos_list)=%d columns_in_page=%d" +
                          "len(datasource.get_current_page())" % (
                          start_x, len(self.x_pos_list),
                          columns_in_page,
                          len(self.datasource.get_current_page())))
        painter.restore()

        return False

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
        if not self.books:
            return False
        self.book_selected.emit(self.which_book(event.x(), event.y()))

    def mouseMoveEvent(self, event):
        if not self.books:
            return False
        # TODO:
        print("which chapter? %d" % self.which_chapter(event.x(), event.y()))

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

    def resizeEvent(self, event):
        super(BookshelfWidget, self).resizeEvent(event)
        self.do_calc()

    def which_book(self, x, y):
        selected = 0
        for r in self.regions:
            if r.contains(QPoint(int(x), int(y))):
                break
            selected = selected+1
        if self.datasource.current_page > 0:
            for page in self.datasource.pages[:self.datasource.current_page]:
                selected = selected + len(page)
        #print("selected={0}".format(selected))
        if selected < len(self.books):
            return self.books[selected][1]
        return None

    def get_book(self, idx):
        return self.books[idx]

if __name__ == "__main__":
    import sys
    from PySide.QtGui import QApplication
    from PySide.QtGui import QMainWindow

    def clicked(book):
        print(book)

    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            self.widget = BookshelfWidget(self, sys.argv[1])
            self.widget.book_selected.connect(clicked)
            self.setCentralWidget(self.widget)
            self.resize(800, 600)

    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    app.exec_()
